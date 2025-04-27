import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from .schema import UnifiedJobSchema
from .utils import get_nested_value, safe_concat

logger = logging.getLogger(__name__)

class StratumWorkMapper:
    """Mapper for stratum.work data format."""
    
    def __init__(self, schema: Optional[UnifiedJobSchema] = None):
        """
        Initialize the mapper.
        
        Args:
            schema: Schema instance to use, or create a new one if None
        """
        self.schema = schema or UnifiedJobSchema()
        self.service_name = "stratum.work"
        self.field_mappings = self.schema.get_mapping_for_service(self.service_name)
    
    def map(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map stratum.work data to unified schema.
        
        Args:
            data: Raw data with metadata
            
        Returns:
            Normalized data according to unified schema
        """
        try:
            # Create empty unified schema
            unified = self.schema.create_empty()
            
            # Set basic metadata
            metadata = data.get("metadata", {})
            unified["source"] = self.service_name
            unified["timestamp"] = metadata.get("received_at", datetime.utcnow().isoformat())
            unified["region"]["source"] = metadata.get("source_region", "unknown")
            unified["region"]["target"] = metadata.get("target_region", "unknown")
            
            # Get the parsed message
            message = data.get("parsed_message", {})
            
            # Apply mappings from config if available
            if self.field_mappings:
                for field, mapping in self.field_mappings.items():
                    if field in unified:
                        # Handle special cases like concatenation
                        if isinstance(mapping, str) and "concat(" in mapping:
                            # Parse concat parameters
                            concat_params = mapping.strip("concat()").split(",")
                            values = []
                            for param in concat_params:
                                param = param.strip()
                                values.append(str(get_nested_value(message, param) or ""))
                            unified[field] = "".join(values)
                        else:
                            # Regular field mapping
                            unified[field] = get_nested_value(message, mapping)
            else:
                # Fallback manual mapping if config not available
                self._apply_manual_mapping(unified, message)
            
            # Store original data in metadata
            unified["metadata"]["original"] = message
            
            return unified
            
        except Exception as e:
            logger.error(f"Error mapping {self.service_name} data: {e}")
            # Return basic info even if mapping fails
            return {
                "source": self.service_name,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": {
                    "original": data.get("parsed_message", {}),
                    "mapping_error": str(e)
                }
            }
    
    def _apply_manual_mapping(self, unified: Dict[str, Any], message: Dict[str, Any]):
        """
        Apply manual mapping as fallback.
        
        Args:
            unified: Unified schema to fill
            message: Source message data
        """
        # Based on expected stratum.work format
        # Note: This is a best guess - adjust with real observed data
        
        # Stratum.work might use a different structure than standard mining.notify
        # Assuming it has a "job" object with job details
        job_data = message.get("job", {})
        
        if job_data and isinstance(job_data, dict):
            # Map standard job fields
            unified["job_id"] = job_data.get("id", "")
            unified["prev_block_hash"] = job_data.get("prevHash", job_data.get("prev_hash", ""))
            
            # Handle coinbase_tx which might be in different formats
            if "coinbase1" in job_data and "coinbase2" in job_data:
                unified["coinbase_tx"] = safe_concat(job_data.get("coinbase1", ""), job_data.get("coinbase2", ""))
            elif "coinbase" in job_data:
                unified["coinbase_tx"] = job_data.get("coinbase", "")
                
            # Handle merkle branches with different possible field names
            merkle_field = next((f for f in ["merkleBranches", "merkle_branches", "merkle"] if f in job_data), None)
            if merkle_field and isinstance(job_data.get(merkle_field), list):
                unified["merkle_branches"] = job_data.get(merkle_field)
                
            # Map remaining standard fields
            unified["version"] = job_data.get("version", "")
            unified["bits"] = job_data.get("bits", job_data.get("nbits", ""))
            unified["time"] = job_data.get("time", job_data.get("ntime", 0))
            unified["height"] = job_data.get("height", 0)
            unified["clean_jobs"] = job_data.get("cleanJobs", job_data.get("clean_jobs", False))
        else:
            # If no job object, try standard mining.notify format
            method = message.get("method", "")
            params = message.get("params", [])
            
            if method == "mining.notify" and isinstance(params, list):
                if len(params) >= 1:
                    unified["job_id"] = params[0]
                if len(params) >= 2:
                    unified["prev_block_hash"] = params[1]
                if len(params) >= 4:
                    unified["coinbase_tx"] = safe_concat(params[2], params[3])
                if len(params) >= 5 and isinstance(params[4], list):
                    unified["merkle_branches"] = params[4]
                if len(params) >= 6:
                    unified["version"] = params[5]
                if len(params) >= 7:
                    unified["bits"] = params[6]
                if len(params) >= 8:
                    unified["time"] = params[7]
                if len(params) >= 9:
                    unified["clean_jobs"] = params[8]
        
        # Handle mining.set_difficulty separately
        if message.get("method") == "mining.set_difficulty" and isinstance(message.get("params", []), list):
            params = message.get("params", [])
            if len(params) >= 1:
                unified["difficulty"] = params[0]
        
        # Try to extract pool information
        pool_info = message.get("pool", {})
        if isinstance(pool_info, dict):
            unified["mining_pool"] = pool_info.get("name", "")
            if not unified["difficulty"] and "difficulty" in pool_info:
                unified["difficulty"] = pool_info.get("difficulty", 0.0)
        elif isinstance(pool_info, str):
            unified["mining_pool"] = pool_info
        
        # If difficulty not yet set, look for it in top-level
        if not unified["difficulty"] and "difficulty" in message:
            unified["difficulty"] = message.get("difficulty", 0.0)
        
        # Stratum.work specific extensions
        if "extensions" in message:
            unified["metadata"]["extensions"] = message.get("extensions", {})
        
        # Add additional data specific to stratum.work if available
        if "region" in message and not isinstance(message["region"], str):
            # Don't overwrite if already set and in the expected format
            unified["metadata"]["geo_info"] = message.get("region", {})
            
        # If we have a field with the pool name but it's not set yet
        if not unified["mining_pool"]:
            for field in ["pool_name", "poolName", "mining_pool"]:
                if field in message and message[field]:
                    unified["mining_pool"] = message[field]
                    break