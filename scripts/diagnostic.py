"""
Diagnostic script for testing core functionality of the stratum monitor.

This script tests the following components incrementally:
1. WebSocket connections to each stratum monitoring service (or mock services)
2. Basic message parsing
3. Data structure verification

Usage:
    python diagnostic.py [--config=config_path] [--use-mock=true/false]
"""

import asyncio
import argparse
import json
import logging
import sys
import os
import yaml
import time
from datetime import datetime
import websockets

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("diagnostic")

# Constants
DEFAULT_MOCK_SERVICES = {
    "miningpool.observer": "ws://localhost:8765",
    "stratum.work": "ws://localhost:8766",
    "mempool.space": "ws://localhost:8767"
}

DEFAULT_REAL_SERVICES = {
    "miningpool.observer": "wss://stratum.miningpool.observer/ws",
    "stratum.work": "wss://stratum.work/ws",
    "mempool.space": "wss://mempool.space/stratum/ws"
}

class DiagnosticTool:
    """Tool for running diagnostics on stratum monitor components."""
    
    def __init__(self, config_path: str = "config/settings.yml", use_mock: bool = True):
        """
        Initialize the diagnostic tool.
        
        Args:
            config_path: Path to the configuration file
            use_mock: Whether to use mock services instead of real ones
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.use_mock = use_mock
        
        # Determine which services to use
        self.services = DEFAULT_MOCK_SERVICES if use_mock else DEFAULT_REAL_SERVICES
        
        # Override with config if available
        if self.config.get("collectors", {}).get("services"):
            for service_name, service_config in self.config.get("collectors", {}).get("services", {}).items():
                if service_name in self.services and "url" in service_config:
                    self.services[service_name] = service_config["url"]
        
        # Save messages received for testing
        self.received_messages = {
            service_name: [] for service_name in self.services
        }
        
        logger.info(f"Using {'mock' if use_mock else 'real'} services")
        for service_name, url in self.services.items():
            logger.info(f"  {service_name}: {url}")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    async def test_connections(self, timeout: int = 30) -> dict:
        """
        Test connections to each stratum monitoring service.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            Dictionary mapping service names to connection status
        """
        logger.info("=== Testing WebSocket Connections ===")
        
        results = {}
        
        for service_name, websocket_url in self.services.items():
            logger.info(f"Testing connection to {service_name} at {websocket_url}")
            
            try:
                success = False
                message_count = 0
                error = None
                
                # Start connection
                try:
                    async with websockets.connect(websocket_url, ping_interval=None) as websocket:
                        logger.info(f"Connected to {service_name}")
                        
                        # Send subscription message (some services require this)
                        try:
                            subscribe_msg = json.dumps({
                                "id": 1,
                                "method": "mining.subscribe",
                                "params": ["stratum-monitor/1.0.0"]
                            })
                            await websocket.send(subscribe_msg)
                            logger.info(f"Sent subscription to {service_name}")
                        except Exception as e:
                            logger.warning(f"Failed to send subscription to {service_name}: {e}")
                        
                        # Wait for messages
                        start_time = time.time()
                        while time.time() - start_time < timeout:
                            try:
                                # Set a timeout for receiving a message
                                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                                
                                # Store message
                                self.received_messages[service_name].append(message)
                                message_count += 1
                                
                                try:
                                    # Try to parse as JSON for logging
                                    parsed = json.loads(message)
                                    logger.info(f"Received message from {service_name}: {json.dumps(parsed, indent=2)[:100]}...")
                                except:
                                    logger.info(f"Received message from {service_name}: {message[:100]}...")
                                
                                # If we've received at least one message, consider it a success
                                success = True
                                
                                # If we've received enough messages, we can stop
                                if message_count >= 3:
                                    break
                                    
                            except asyncio.TimeoutError:
                                logger.info(f"Waiting for messages from {service_name}...")
                                # Continue waiting
                        
                        logger.info(f"Received {message_count} messages from {service_name}")
                        
                except Exception as e:
                    error = str(e)
                    logger.error(f"Error connecting to {service_name}: {e}")
                
                # Store results
                results[service_name] = {
                    "success": success,
                    "message_count": message_count,
                    "error": error
                }
                
                if success:
                    logger.info(f"✅ Successfully connected to {service_name}")
                else:
                    logger.error(f"❌ Failed to connect to {service_name}: {error}")
                
            except Exception as e:
                logger.error(f"Unexpected error testing {service_name}: {e}")
                results[service_name] = {
                    "success": False,
                    "message_count": 0,
                    "error": str(e)
                }
        
        # Print summary
        logger.info("=== Connection Test Results ===")
        for service, result in results.items():
            status = "✅ Connected" if result["success"] else "❌ Failed"
            detail = f"({result['message_count']} messages)" if result["success"] else f"({result['error']})"
            logger.info(f"{service}: {status} {detail}")
        
        return results
    
    def test_message_structure(self) -> dict:
        """
        Test the structure of received messages.
        
        Returns:
            Dictionary with test results
        """
        logger.info("=== Testing Message Structure ===")
        
        results = {}
        
        for service_name, messages in self.received_messages.items():
            if not messages:
                logger.warning(f"No messages available for {service_name}")
                results[service_name] = {
                    "success": False,
                    "error": "No messages received"
                }
                continue
            
            try:
                # Check first message structure
                message = messages[0]
                
                # Try to parse as JSON
                try:
                    parsed = json.loads(message)
                    
                    # Check for basic stratum protocol fields
                    has_method = "method" in parsed
                    has_params = "params" in parsed
                    has_id = "id" in parsed
                    
                    # Check for common mining job fields
                    has_job = (
                        (has_method and parsed["method"] == "mining.notify") or
                        ("job" in parsed) or
                        (has_params and len(parsed.get("params", [])) >= 8)
                    )
                    
                    # Determine success
                    success = has_method or has_job
                    
                    # Log details
                    if success:
                        logger.info(f"✅ {service_name} message has valid structure")
                        if has_method:
                            logger.info(f"  Method: {parsed.get('method')}")
                        if has_params:
                            logger.info(f"  Parameters: {len(parsed.get('params', []))} items")
                        if "pool" in parsed:
                            pool_info = parsed.get("pool")
                            if isinstance(pool_info, dict):
                                logger.info(f"  Pool: {pool_info.get('name', 'unknown')}")
                            else:
                                logger.info(f"  Pool: {pool_info}")
                        if "height" in parsed:
                            logger.info(f"  Height: {parsed.get('height')}")
                    else:
                        logger.warning(f"❌ {service_name} message has unexpected structure")
                    
                    results[service_name] = {
                        "success": success,
                        "has_method": has_method,
                        "has_params": has_params,
                        "has_id": has_id,
                        "has_job": has_job,
                        "message_sample": {k: v for k, v in parsed.items() if k in ["method", "id"]}
                    }
                    
                except json.JSONDecodeError:
                    logger.error(f"❌ {service_name} message is not valid JSON")
                    results[service_name] = {
                        "success": False,
                        "error": "Message is not valid JSON"
                    }
            
            except Exception as e:
                logger.error(f"Error analyzing {service_name} message: {e}")
                results[service_name] = {
                    "success": False,
                    "error": str(e)
                }
        
        # Print summary
        logger.info("=== Message Structure Test Results ===")
        for service, result in results.items():
            status = "✅ Valid" if result.get("success", False) else "❌ Invalid"
            logger.info(f"{service}: {status}")
        
        return results
    
    def analyze_message_contents(self) -> dict:
        """
        Analyze the contents of received messages.
        
        Returns:
            Dictionary with analysis results
        """
        logger.info("=== Analyzing Message Contents ===")
        
        results = {}
        
        for service_name, messages in self.received_messages.items():
            if not messages:
                logger.warning(f"No messages available for {service_name}")
                results[service_name] = {"error": "No messages received"}
                continue
            
            try:
                # Initialize service results
                service_results = {
                    "message_count": len(messages),
                    "mining_pools": set(),
                    "heights": set(),
                    "methods": set()
                }
                
                # Analyze each message
                for message in messages:
                    try:
                        parsed = json.loads(message)
                        
                        # Extract method
                        if "method" in parsed:
                            service_results["methods"].add(parsed["method"])
                        
                        # Extract pool info
                        if "pool" in parsed:
                            pool_info = parsed["pool"]
                            if isinstance(pool_info, dict) and "name" in pool_info:
                                service_results["mining_pools"].add(pool_info["name"])
                            elif isinstance(pool_info, str):
                                service_results["mining_pools"].add(pool_info)
                        
                        # Extract height
                        if "height" in parsed:
                            height = parsed["height"]
                            if height is not None:
                                service_results["heights"].add(height)
                        
                    except json.JSONDecodeError:
                        # Skip non-JSON messages
                        continue
                
                # Convert sets to lists for JSON serialization
                service_results["mining_pools"] = list(service_results["mining_pools"])
                service_results["heights"] = list(service_results["heights"])
                service_results["methods"] = list(service_results["methods"])
                
                # Log results
                logger.info(f"{service_name} analysis:")
                logger.info(f"  Message count: {service_results['message_count']}")
                logger.info(f"  Mining pools: {', '.join(service_results['mining_pools']) or 'None'}")
                logger.info(f"  Methods: {', '.join(service_results['methods']) or 'None'}")
                logger.info(f"  Heights: {', '.join(str(h) for h in service_results['heights']) or 'None'}")
                
                results[service_name] = service_results
                
            except Exception as e:
                logger.error(f"Error analyzing {service_name} messages: {e}")
                results[service_name] = {"error": str(e)}
        
        return results
    
    async def run_minimal_test(self) -> dict:
        """
        Run a minimal test of core functionality.
        
        Returns:
            Dictionary with test results
        """
        results = {}
        
        # Step 1: Test connections
        logger.info("\n=== Step 1: Testing WebSocket Connections ===")
        connection_results = await self.test_connections()
        results["connections"] = connection_results
        
        # Check if at least one connection succeeded
        if not any(result["success"] for result in connection_results.values()):
            logger.error("❌ All connections failed, cannot proceed with further tests")
            return results
        
        # Step 2: Test message structure
        logger.info("\n=== Step 2: Testing Message Structure ===")
        structure_results = self.test_message_structure()
        results["structure"] = structure_results
        
        # Step 3: Analyze message contents
        logger.info("\n=== Step 3: Analyzing Message Contents ===")
        content_results = self.analyze_message_contents()
        results["contents"] = content_results
        
        # Print overall summary
        logger.info("\n=== Overall Test Summary ===")
        connection_success = any(result["success"] for result in connection_results.values())
        structure_success = any(result.get("success", False) for result in structure_results.values())
        
        logger.info(f"Connection Tests: {'✅ Passed' if connection_success else '❌ Failed'}")
        logger.info(f"Structure Tests: {'✅ Passed' if structure_success else '❌ Failed'}")
        logger.info(f"Content Analysis: {'✅ Completed' if content_results else '❌ Failed'}")
        
        overall_success = connection_success and structure_success
        logger.info(f"Overall: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        
        # Suggestions for next steps
        if overall_success:
            logger.info("\n=== Next Steps ===")
            logger.info("1. Implement the data normalization layer based on the message structures seen")
            logger.info("2. Create a WebSocket client that can maintain long-running connections")
            logger.info("3. Implement a storage solution for saving normalized job data")
            logger.info("4. Develop analysis components for comparing jobs across services")
        
        return results


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Stratum Monitor Diagnostic Tool")
    parser.add_argument("--config", default="config/settings.yml", help="Path to configuration file")
    parser.add_argument("--use-mock", type=lambda x: x.lower() == 'true', default=True, 
                      help="Whether to use mock services (true/false)")
    args = parser.parse_args()
    
    # Create diagnostic tool
    diagnostic = DiagnosticTool(config_path=args.config, use_mock=args.use_mock)
    
    # Run the minimal test
    await diagnostic.run_minimal_test()


if __name__ == "__main__":
    asyncio.run(main())