# base client functionality

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional, List, Callable, asyncio

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(_name_)

class BaseStratumClient:
    """This base client is supposed to connect the stratum monitoring services"""

    def _init_(
        self,
        service_name: str,
        websocket_url: str,
        message_handler: callable,
        reconnect_interval: float = 5.0,
        max_reconnect_interval: float = 60.0,
        reconnect_factor: float = 1.5,
        source_origin: str = "unknown",
        target_origin: str = "unknown"
    ):
        """
        Initializing the stratum client

        Args: 
            service_name: Identifies the service i.e stratum.work
            websocket_url: Websocket URL to connect to
            message_handler: Callback function to process received messages
            reconnect_interval: Initial reconnection interval in seconds
            max_reconnect_interval: Maximum reconnection interval in seconds
            reconnect_factor: Factor to increase reconnection interval on failure
            source_region: Region where client is being operated
            target_region: Region where stratum service monitoring happens

        """

        self.service_name = service_name
        self.websocket_url = websocket_url
        self.message_handler = message_handler
        self.reconnect_interval  = reconnect_interval
        self.initial_reconnect_interval = reconnect_interval
        self.max_reconnect_interval = max_reconnect_interval
        self.reconnect_factor = reconnect_factor
        self.websocket = None
        self.should_run = True
        self.source_region = source_region
        self.target_region = target_region
        self.connection_attempts = 0
        self.connected_at: Optional[float] = None
        self.messages_received = 0
        self.last_message_at: Optional[float] = None

    async def connect(self):     

