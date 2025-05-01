# Analyze schemas from raw data
"""
Schema analyzer for stratum monitor services.

This script analyzes JSON messages from various stratum monitoring services
to help identify and document their schema structures.
"""

import asyncio
import argparse
import json
import logging
import sys
import os
import yaml
from datetime import datetime
from typing import Dict, Any, List, Set, Optional
from collections import defaultdict

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors.base_client import BaseStratumClient
from src.collectors.observer_client import MiningPoolObserverClient
from src.collectors.stratum_work_client import StratumWorkClient
from src.collectors.mempool_client import MempoolSpaceClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("schema_analyzer.log")
    ]
)
logger = logging.getLogger(__name__)

class SchemaAnalyzer:
    """Analyzes JSON schemas from stratum monitor services."""
    
    def __init__(self, output_dir: str = "schemas"):
        """
        Initialize the schema analyzer.
        
        Args:
            output_dir: Directory to store schema analysis results
        """
        self.output_dir = output_dir
        self.messages = defaultdict(list)
        self.field_types = defaultdict(lambda: defaultdict(set))
        self.field_values = defaultdict(lambda: defaultdict(list))
        self.message_types = defaultdict(set)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    async def collect_messages(self, service_name: str, client: BaseStratumClient, max_messages: int = 100, timeout: int = 300):
        """
        Collect messages from a service.
        
        Args:
            service_name: Name of the service
            client: WebSocket client for the service
            max_messages: Maximum number of messages to collect
            timeout: Timeout in seconds
        """
        logger.info(f"Collecting messages from {service_name}...")
        
        # Set up message handler
        async def message_handler(message: Dict[str, Any]):
            if len(self.messages[service_name]) >= max_messages:
                return
            
            # Store the message
            self.messages[service_name].append(message)
            logger.info(f"Collected message {len(self.messages[service_name])}/{max_messages} from {service_name}")
            
            # If we've collected enough messages, stop the client
            if len(self.messages[service_name]) >= max_messages:
                await client.stop()
        
        # Set client's message handler
        client.message_handler = message_handler
        
        # Connect and wait for messages
        connect_task = asyncio.create_task(client.connect())
        
        try:
            # Wait for either max messages or timeout
            await asyncio.wait_for(connect_task, timeout=timeout)
        except asyncio.TimeoutError:
            logger.info(f"Timeout reached for {service_name}, collected {len(self.messages[service_name])} messages")
            await client.stop()
        except Exception as e:
            logger.error(f"Error collecting messages from {service_name}: {e}")
            await client.stop()
    
    def analyze_schemas(self):
        """Analyze collected messages to identify schema patterns."""
        logger.info("Analyzing message schemas...")
        
        for service_name, messages in self.messages.items():
            logger.info(f"Analyzing {len(messages)} messages from {service_name}")
            
            for message in messages:
                parsed_message = message.get("parsed_message", {})
                
                # Identify message type
                message_type = self._get_message_type(parsed_message)
                if message_type:
                    self.message_types[service_name].add(message_type)
                
                # Analyze field types and values
                self._analyze_fields(service_name, "", parsed_message)
        
        logger.info("Schema analysis complete")
    
    def _get_message_type(self, message: Dict[str, Any]) -> str:
        """
        Determine the type of a message.
        
        Args:
            message: Message to analyze
            
        Returns:
            Message type string
        """
        # Different services may use different fields to indicate message type
        # Common fields include "method", "type", "action", etc.
        for type_field in ["method", "type", "action", "command", "event"]:
            if type_field in message and isinstance(message[type_field], str):
                return f"{type_field}:{message[type_field]}"
        
        # If we can't determine a type, use a hash of the keys
        keys = sorted(message.keys())
        return f"keys:{'-'.join(keys)}" if keys else "unknown"
    
    def _analyze_fields(self, service_name: str, prefix: str, obj: Any):
        """
        Recursively analyze fields in a message.
        
        Args:
            service_name: Name of the service
            prefix: Field path prefix
            obj: Object to analyze
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                self._record_field_info(service_name, field_path, value)
                self._analyze_fields(service_name, field_path, value)
        elif isinstance(obj, list) and obj:
            # For lists, analyze the first item as representative
            field_path = f"{prefix}[]"
            self._record_field_info(service_name, field_path, obj[0])
            self._analyze_fields(service_name, field_path, obj[0])
    
    def _record_field_info(self, service_name: str, field_path: str, value: Any):
        """
        Record type and sample values for a field.
        
        Args:
            service_name: Name of the service
            field_path: Path to the field
            value: Field value
        """
        # Record type
        type_name = type(value).__name__
        self.field_types[service_name][field_path].add(type_name)
        
        # Record sample values (limited to avoid excessive storage)
        if len(self.field_values[service_name][field_path]) < 10:
            # For complex types, just store type info
            if isinstance(value, (dict, list)):
                if isinstance(value, dict):
                    self.field_values[service_name][field_path].append(f"dict with {len(value)} keys")
                else:
                    self.field_values[service_name][field_path].append(f"list with {len(value)} items")
            else:
                # For simple types, store the actual value
                str_value = str(value)
                # Truncate very long values
                if len(str_value) > 100:
                    str_value = f"{str_value[:97]}..."
                self.field_values[service_name][field_path].append(str_value)
    
    def generate_schema_mapping(self) -> Dict[str, Any]:
        """
        Generate a schema mapping configuration.
        
        Returns:
            Schema mapping configuration
        """
        logger.info("Generating schema mapping configuration...")
        
        # Create unified schema based on common fields
        unified_schema = {}
        
        # Define core fields we expect in all services
        core_fields = {
            "source": "string",
            "timestamp": "string",
            "job_id": "string",
            "mining_pool": "string",
            "difficulty": "number",
            "prev_block_hash": "string",
            "coinbase_tx": "string",
            "merkle_branches": "array",
            "version": "string",
            "bits": "string",
            "time": "number",
            "height": "number",
            "clean_jobs": "boolean",
            "region": {
                "source": "string",
                "target": "string"
            },
            "metadata": "object"
        }
        
        # Add core fields to unified schema
        unified_schema["unified_schema"] = core_fields
        
        # Generate mappings for each service
        for service_name in self.messages.keys():
            service_mappings = {}
            
            # Identify potential mappings for each core field
            for field, type_info in core_fields.items():
                if isinstance(type_info, dict):
                    # Skip nested objects for now
                    continue
                
                # Find potential field matches based on field name patterns
                potential_matches = self._find_potential_field_matches(service_name, field)
                
                if potential_matches:
                    # Use the first potential match
                    service_mappings[field] = potential_matches[0]
            
            # Add service mappings
            unified_schema[service_name] = service_mappings
        
        return unified_schema
    
    def _find_potential_field_matches(self, service_name: str, target_field: str) -> List[str]:
        """
        Find potential field matches in a service's messages.
        
        Args:
            service_name: Name of the service
            target_field: Target field name
            
        Returns:
            List of potential field paths
        """
        potential_matches = []
        
        # Check for exact field name match
        for field_path in self.field_types[service_name].keys():
            field_name = field_path.split(".")[-1]
            
            # Strip array notation if present
            if field_name.endswith("[]"):
                field_name = field_name[:-2]
            
            # Check for exact match
            if field_name == target_field:
                potential_matches.append(field_path)
            
            # Check for camelCase variants
            elif field_name.lower() == target_field.lower():
                potential_matches.append(field_path)
            
            # Check for specific fields with known aliases
            elif target_field == "prev_block_hash" and field_name in ["prevHash", "previousblockhash"]:
                potential_matches.append(field_path)
            elif target_field == "job_id" and field_name in ["id", "jobId"]:
                potential_matches.append(field_path)
            elif target_field == "mining_pool" and field_name in ["pool", "poolName"]:
                potential_matches.append(field_path)
            elif target_field == "merkle_branches" and field_name in ["merkle", "merkleBranches"]:
                potential_matches.append(field_path)
        
        # For nested fields, look for common patterns
        if "." not in target_field:
            for field_path in self.field_types[service_name].keys():
                # Look for fields in nested structures
                parts = field_path.split(".")
                for i, part in enumerate(parts):
                    if part == target_field or part.lower() == target_field.lower():
                        # Found a match in a nested structure
                        potential_matches.append(field_path)
        
        # Special case for coinbase_tx which might be composed of multiple fields
        if target_field == "coinbase_tx":
            for field_path in self.field_types[service_name].keys():
                field_name = field_path.split(".")[-1]
                if field_name in ["coinbase1", "coinbase2"]:
                    # Check if both coinbase1 and coinbase2 exist
                    base_path = field_path[:-len(field_name)]
                    if (f"{base_path}coinbase1" in self.field_types[service_name] and 
                        f"{base_path}coinbase2" in self.field_types[service_name]):
                        # Add as a concatenation
                        potential_matches.append(f"concat({base_path}coinbase1, {base_path}coinbase2)")
                        break
        
        return potential_matches
    
    def save_results(self):
        """Save analysis results to files."""
        logger.info(f"Saving results to {self.output_dir}")
        
        # Save raw messages
        for service_name, messages in self.messages.items():
            with open(f"{self.output_dir}/{service_name}_messages.json", "w") as f:
                json.dump(messages, f, indent=2)
        
        # Save field types
        with open(f"{self.output_dir}/field_types.json", "w") as f:
            # Convert sets to lists for JSON serialization
            serializable_types = {}
            for service, fields in self.field_types.items():
                serializable_types[service] = {
                    field: list(types) for field, types in fields.items()
                }
            json.dump(serializable_types, f, indent=2)
        
        # Save field values
        with open(f"{self.output_dir}/field_values.json", "w") as f:
            json.dump(dict(self.field_values), f, indent=2)
        
        # Save message types
        with open(f"{self.output_dir}/message_types.json", "w") as f:
            serializable_types = {
                service: list(types) for service, types in self.message_types.items()
            }
            json.dump(serializable_types, f, indent=2)
        
        # Generate and save schema mapping
        schema_mapping = self.generate_schema_mapping()
        with open(f"{self.output_dir}/schema_mapping.yml", "w") as f:
            yaml.dump(schema_mapping, f, default_flow_style=False)
        
        logger.info("Results saved successfully")

async def run_analyzer(config: Dict[str, Any], output_dir: str, max_messages: int, timeout: int):
    """
    Run the schema analyzer.
    
    Args:
        config: Configuration dictionary
        output_dir: Directory to store analysis results
        max_messages: Maximum messages to collect per service
        timeout: Collection timeout in seconds
    """
    # Create analyzer
    analyzer = SchemaAnalyzer(output_dir=output_dir)
    
    # Create clients
    source_region = config.get("monitor", {}).get("region", "unknown")
    clients = {
        "miningpool.observer": MiningPoolObserverClient(
            message_handler=lambda x: None,  # Will be replaced by analyzer
            source_region=source_region,
            config_path=None  # Will use client's default config
        ),
        "stratum.work": StratumWorkClient(
            message_handler=lambda x: None,
            source_region=source_region,
            config_path=None
        ),
        "mempool.space": MempoolSpaceClient(
            message_handler=lambda x: None,
            source_region=source_region,
            config_path=None
        )
    }
    
    # Collect messages from each service
    for service_name, client in clients.items():
        await analyzer.collect_messages(service_name, client, max_messages, timeout)
    
    # Analyze schemas
    analyzer.analyze_schemas()
    
    # Save results
    analyzer.save_results()

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Schema analyzer for stratum monitor services")
    parser.add_argument("--config", default="../config/settings.yml", help="Path to configuration file")
    parser.add_argument("--output-dir", default="schemas", help="Directory to store analysis results")
    parser.add_argument("--max-messages", type=int, default=100, help="Maximum messages to collect per service")
    parser.add_argument("--timeout", type=int, default=300, help="Collection timeout in seconds")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Run analyzer
    asyncio.run(run_analyzer(config, args.output_dir, args.max_messages, args.timeout))

if __name__ == "__main__":
    main()