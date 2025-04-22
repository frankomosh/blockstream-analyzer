# miningpool.observer specific mapper
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from .schema import UnifiedJobSchema
from .utils import get_nested_value, safe_concat

logger = logging.getLogger(__name__)

class MiningPoolObserverMapper:
    """Mapper for miningpool.observer data format."""
    
    def __init__(self, schema: Optional[UnifiedJobSchema] = None):
        """
        Initialize the mapper.
        
        Args:
            schema: Schema instance to use, or create a new one if None
        """
        self.schema = schema or UnifiedJobSchema()
        self.service_name = "miningpool.observer"
        self.field_mappings = self.schema.get_mapping_for_service(self.service_name)
    
    def map(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map miningpool.observer data to unified schema.
        
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
                # Fallback manual mapping if config is not available
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
        # Extract fields based on miningpool.observer's format
        # This is a hypothetical mapping - adjust based on actual format
        method = message.get("method", "")
        params = message.get("params", [])
        
        if method == "mining.notify" and isinstance(params, list):
            if len(params) >= 1:
                unified["job_id"] = params[0]
            if len(params) >= 2:
                unified["prev_block_hash"] = params[1]
            if len(params) >= 4:
                unified["coinbase_tx"] = safe_concat(params[2], params[3])
            if len(params) >= 5:
                unified["merkle_branches"] = params[4]
            if len(params) >= 6:
                unified["version"] = params[5]
            if len(params) >= 7:
                unified["bits"] = params[6]
            if len(params) >= 8:
                unified["time"] = params[7]
            if len(params) >= 9:
                unified["clean_jobs"] = params[8]
        
        # Try to extract pool information if available
        pool_info = message.get("pool", {})
        if isinstance(pool_info, dict):
            unified["mining_pool"] = pool_info.get("name", "")
            unified["difficulty"] = pool_info.get("difficulty", 0.0)
        elif isinstance(pool_info, str):
            unified["mining_pool"] = pool_info
        
        # Try to extract block height if available
        if "height" in message:
            unified["height"] = message.get("height", 0)