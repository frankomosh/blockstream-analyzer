# WebSocket client for mempool.space stratum monitoring
import logging
import json
from typing import Callable, Dict, Any, Optional

import yaml

from .base_client import BaseStratumClient

logger = logging.getLogger(__name__)

class MempoolSpaceClient(BaseStratumClient):
    """Client for mempool.space/stratum service."""
    
    def __init__(
        self,
        message_handler: Callable,
        source_region: str = "unknown",
        config_path: str = "config/settings.yml"
    ):
        """
        Initialize the mempool.space client.
        
        Args:
            message_handler: Callback function to process received messages
            source_region: Region where this client is running
            config_path: Path to configuration file
        """
        # Load config
        config = self._load_config(config_path)
        
        # Get service specific settings
        service_config = config.get("collectors", {}).get("services", {}).get("mempool.space", {})
        websocket_url = service_config.get("url", "wss://mempool.space/stratum/ws")
        target_region = service_config.get("target_region", "global")
        
        # Get general collector settings
        reconnect_interval = config.get("collectors", {}).get("reconnect_interval", 5.0)
        max_reconnect_interval = config.get("collectors", {}).get("max_reconnect_interval", 60.0)
        reconnect_factor = config.get("collectors", {}).get("reconnect_factor", 1.5)
        
        super().__init__(
            service_name="mempool.space",
            websocket_url=websocket_url,
            message_handler=message_handler,
            reconnect_interval=reconnect_interval,
            max_reconnect_interval=max_reconnect_interval,
            reconnect_factor=reconnect_factor,
            source_region=source_region,
            target_region=target_region,
        )
        
        # Service-specific state
        self.subscription_sent = False
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    async def connect(self):
        """Connect and handle service-specific connection requirements."""
        # If mempool.space requires subscription or authentication,
        # implement the service-specific logic here
        await super().connect()
    
    async def _process_messages(self):
        """Process incoming messages with service-specific preprocessing."""
        if not self.websocket:
            return
        
        # If mempool.space needs subscription after connection
        if not self.subscription_sent and self.websocket:
            try:
                # Example: Some services might require subscription
                # This is hypothetical - adjust based on actual requirements
                subscription_msg = json.dumps({
                    "id": 1,
                    "method": "mining.subscribe",
                    "params": ["stratum-monitor/1.0.0"]
                })
                await self.websocket.send(subscription_msg)
                self.subscription_sent = True
                logger.info(f"Sent subscription to {self.service_name}")
            except Exception as e:
                logger.error(f"Error sending subscription to {self.service_name}: {e}")
        
        # Process messages
        await super()._process_messages()