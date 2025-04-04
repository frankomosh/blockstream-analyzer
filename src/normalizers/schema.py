# Unified schema definition
import logging
import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class UnifiedJobSchema:
    """Definition of unified job schema for stratum monitoring"""

    def __init__(self, schema_path: str = "config/schema_mappings.yml"):
        """
        Initialize the unified schema

        Args:
            schema_path: Path to schema mapping configuration
        """
        self.schema_path = schema_path
        self.schema_config = self._load_schema_config(schema_path)
        self.schema = self.schema_config.get("unified_schema", {})

        # Define default schema if not loaded from config

        if not self.schema:
            self.schema = {
                "source": "",                # Source service name
                "timestamp": "",             # ISO-8601 timestamp when received
                "job_id": "",                # Job identifier
                "mining_pool": "",           # Name of the mining pool
                "difficulty": 0.0,           # Mining difficulty
                "prev_block_hash": "",       # Previous block hash
                "coinbase_tx": "",           # Coinbase transaction
                "merkle_branches": [],       # Merkle branches array
                "version": "",               # Block version
                "bits": "",                  # Difficulty bits
                "time": 0,                   # Block time
                "height": 0,                 # Block height
                "clean_jobs": False,         # Clean jobs flag
                "region": {
                    "source": "",            # Region of the client
                    "target": ""             # Region of the service
                },
                "metadata": {}               # Source-specific fields

            }
    def _load_schema_config(self, schema_path: str) -> Dict[str, Any]:
        """Load schema configuration from YAML file"""
        try: 
            with open(schema_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading schema configuration: {e}")
            return {}

    def create_empty(self) -> Dict[str, Any]:
        """Create an empty schema instance."""
        # Deep copy to avoid shared references
        empty_schema = {}
        for key, value in self.schema.items():
            if isinstance(value, dict):
                empty_schema[key] = {}
                for subkey, subvalue in value.items():
                    empty_schema[key][subkey] = self._copy_value(subvalue)
            else:
                empty_schema[key] = self._copy_value(value)
        return empty_schema

    def _copy_value(self, value: Any) -> Any:
        """Create a copy of a value with appropriate default."""
        if isinstance(value, str):
            return ""
        elif isinstance(value, (int, float)):
            return 0
        elif isinstance(value, bool):
            return False
        elif isinstance(value, list):
            return []
        elif isinstance(value, dict):
            return {}
        else:
            return None

    def get_mapping_for_service(self, service_name: str) -> Dict[str, Any]:
        """
        Get field mappings for a specific service

        Args:
            service_name: Name of service

        Returns:
            Dictionary of field mappings
        """                             
        return self.schema_config.get(service_name, {})

    def validate(self, job:Dict[str, Any]) -> bool:
        """
        Validate a job against the schema.

        Args:
            job: Job data to validate

        Returns:
            True if valid, False otherwise    
        """    
        # Basic validation - check required fields
        for field in ["source", "timestamp", "job_id"]:
            if field not in job or not job[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        return True        
