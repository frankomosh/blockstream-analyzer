# WebSocket client for observer client
import logging
from typing import Callable, Dict, Any, Optional

import yaml

from .base_client import BaseStratumClient

logger = logging.getLogger(__name__)

class MiningPoolObserver(BaseStratumClient):
    """Client for stratum.miningpool.observer service"""
    def __init__(
        self,
        message_handler: Callable,
        source_region: str = "unknown",
        config_path: str = "config/settings.yml"
    ):
        """

        Initialize the MiningPoolObserver client

        Args:
            message_handler: Callback function to process received messages
            source_region: Region where the client is running
            config_path: Path to configuration file
        """
        # Load config

        # Get service specific settings
        service_config = config.get("collectors", {}).get("services", {}).get("miningpool.observer", {})
        websocket_url = service_config.get("url", "wss://stratum.miningpool.observer/ws")
        target_region = service_config.get("target_region", "global")

        # Get general collector settings
        reconnect_interval = config.get("collectors", {}).get("reconnect_interval", 5.0)
        max_reconnect_interval = config.get("collectors", {}).get("max_reconnect_interval", 60.0)
        reconnect_factor = config.get("collectors", {}).get("reconnect_factor", 1.5)

        super().__init__(
            service_name="miningpool.observer",
            websocket_url=websocket_url,
            message_handler=message_handler,
            reconnect_interval=reconnect_interval,
            max_reconnect_interval=max_reconnect_interval,
            reconnect_factor=reconnect_factor,
            source_region=source_region,
            target_region=target_region,

        )
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}

    async def _process_messages(self):
        """
        Processes incoming websocket messages with service-specific handling.
        Method can be extended to add service-specific preprocessing before passing to the general handler
        """     
        await super()._process_messages()           
