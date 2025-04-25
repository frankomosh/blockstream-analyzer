# Application entry point
import asyncio
import logging
import signal
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, List

# Import components
from src.collectors.observer_client import MiningPoolObserverClient
from src.collectors.stratum_work_client import StratumWorkClient
from src.collectors.mempool_client import MempoolSpaceClient
from src.normalizers.data_normalizer import DataNormalizer
from src.analysis.job_comparator import JobComparator
from src.storage.db import DatabaseManager
from src.api.routes import start_api_server

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("stratum_monitor.log")
    ]
)
logger = logging.getLogger(__name__)

class StratumMonitorApp:
    """Main application for stratum monitor comparison."""
    
    def __init__(self, config_path: str = "config/settings.yml"):
        """
        Initialize the application.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        
        # Configure logging
        log_level = self.config.get("monitor", {}).get("log_level", "INFO")
        logging.getLogger().setLevel(getattr(logging, log_level))
        
        # Initialize components
        self.normalizer = DataNormalizer(
            schema_path=self.config.get("normalizers", {}).get("schema_mapping", "config/schema_mappings.yml")
        )
        
        self.comparator = JobComparator(
            time_window=self.config.get("analysis", {}).get("time_window", 300.0)
        )
        
        self.db = DatabaseManager(
            connection_string=self.config.get("database", {}).get("connection_string", "mongodb://localhost:27017"),
            database_name=self.config.get("database", {}).get("database_name", "stratum_monitor")
        )
        
        # Initialize clients
        self.clients = []
        self.running = False
        self.stats_interval = self.config.get("analysis", {}).get("stats_interval", 60.0)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    async def _initialize_clients(self):
        """Initialize WebSocket clients."""
        source_region = self.config.get("monitor", {}).get("region", "unknown")
        
        # Create clients
        self.clients = [
            MiningPoolObserverClient(
                message_handler=self._handle_message,
                source_region=source_region,
                config_path=self.config_path
            ),
            StratumWorkClient(
                message_handler=self._handle_message,
                source_region=source_region,
                config_path=self.config_path
            ),
            MempoolSpaceClient(
                message_handler=self._handle_message,
                source_region=source_region,
                config_path=self.config_path
            )
        ]
    
    async def _handle_message(self, message: Dict[str, Any]):
        """
        Handle incoming WebSocket messages.
        
        Args:
            message: Raw message with metadata
        """
        try:
            # Store raw message
            await self.db.store_raw_message(message)
            
            # Normalize message
            normalized = await self.normalizer.normalize(message)
            if normalized:
                # Store normalized message
                await self.db.store_normalized_job(normalized)
                
                # Process for analysis
                await self.comparator.process_job(normalized)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _periodic_stats(self):
        """Periodically calculate and store statistics."""
        while self.running:
            try:
                # Calculate statistics
                stats = self.comparator.get_statistics()
                
                # Store statistics
                await self.db.store_stats(stats)
                
                # Log summary
                sources = stats.get("sources", {})
                logger.info(
                    f"Stats update - "
                    f"Observer: {sources.get('miningpool.observer', {}).get('recent_job_count', 0)} jobs, "
                    f"Stratum.work: {sources.get('stratum.work', {}).get('recent_job_count', 0)} jobs, "
                    f"Mempool: {sources.get('mempool.space', {}).get('recent_job_count', 0)} jobs"
                )
            except Exception as e:
                logger.error(f"Error calculating stats: {e}")
            
            # Wait for next interval
            await asyncio.sleep(self.stats_interval)
    
    async def start(self):
        """Start the application."""
        self.running = True
        
        try:
            # Initialize database
            await self.db.initialize()
            
            # Initialize clients
            await self._initialize_clients()
            
            # Start client connections
            client_tasks = [asyncio.create_task(client.connect()) for client in self.clients]
            
            # Start statistics calculation
            stats_task = asyncio.create_task(self._periodic_stats())
            
            # Start API server
            api_server_task = asyncio.create_task(
                start_api_server(
                    host=self.config.get("api", {}).get("host", "0.0.0.0"),
                    port=self.config.get("api", {}).get("port", 8080),
                    comparator=self.comparator,
                    db=self.db,
                    origins=self.config.get("api", {}).get("cors_origins", [])
                )
            )
            
            # Wait for all tasks
            await asyncio.gather(*client_tasks, stats_task, api_server_task)
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop the application."""
        self.running = False
        
        # Stop clients
        for client in self.clients:
            await client.stop()
        
        # Close database connection
        await self.db.close()
        
        logger.info("Application stopped")


def main():
    """Main entry point."""
    # Create application instance
    app = StratumMonitorApp()
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(app.stop()))
    
    # Run the application
    try:
        loop.run_until_complete(app.start())
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        loop.close()


if __name__ == "__main__":
    main()