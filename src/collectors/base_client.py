# base client functionality

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional, List, Callable, Any

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)

class BaseStratumClient:
    """This base client is supposed to connect the stratum monitoring services"""

    def __init__(
        self,
        service_name: str,
        websocket_url: str,
        message_handler: Callable,
        reconnect_interval: float = 5.0,
        max_reconnect_interval: float = 60.0,
        reconnect_factor: float = 1.5,
        source_region: str = "unknown",
        target_region: str = "unknown"
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
        """The websocket connection should have exponetial backoff."""
        self.connection_attempts += 1
        current_interval = self.reconnect_interval

        while self.should_run:
            try:
                logger.info(f"Connecting to {self.service_name} at {self.websocket_url}")

                async with websockets.connect(self.websocket_url) as websocket:
                    self.websocket = websocket
                    self.connected_at = time.time()
                    logger.info(f"Connected to {self.service_name}")

                    # On successful connection, connection interval should be reconnected
                    self.reconnect_interval = self.initial_reconnect_interval

                    # Process the messages until the connection is closed
                    await self._process_messages()

            except ConnectionClosed as e:
                logger.warning(f"Connection to {self.service_name} closed: {e}")
            except Exception as e:
                logger.error(f"Error in connection to {self.service_name}: {e}")  

            if not self.should_run:
                break

        # Implementing exponential backoff            
        logger.info(f"Reconnecting to {self.service_name} in {current_interval:.1f}s")
        await asyncio.sleep(current_interval)

        # Increase reconnection interval
        current_interval = min(
            current_interval * self.reconnect_factor,
            self.max_reconnect_interval
        )               
        self.reconnect_interval = current_interval

    async def _process_messages(self): 
        """Processing for incoming websocket messages"""
        if not self.websocket:
            return

        async for message in self.websocket:
            self.messages_received += 1
            self.last_message_at = time.time()

            # Parsing JSON message 
            try: 
                parsed_message = json.loads(message)

                # Adding metadata to the message
                enriched_message = {
                    "raw_message": message,
                    "parsed_message": parsed_message,
                    "metadata":{
                        "service_name": self.service_name,
                        "received_at": datetime.utcnow().isoformat(),
                        "received_timestamp": self.last_message_at,
                        "source_region": self.source_region,
                        "target_region": self.target_region,
                    }
                }

                # Pass to handler
                await self.message_handler(enriched_message)    

            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message from {self.service_name}: {message[:100]}...")
            except Exception as e:
                logger.error(f"Error processing message from {self.service_name}: {e}")

    async def stop(self):
        """Stop client and close connection"""
        self.should_run = False
        if self.websocket:
            await self.websocket.close()

    def get_status(self) -> Dict[str, Any]:
        """Get client status information"""
        return {
            "service_name": self.service_name,
            "websocket_url": self.websocket_url,
            "connected": self.websocket is not None and not self.websocket.closed,
            "connection_attempts": self.connection_attempts,
            "connected_at": self.connected_at,
            "messages_received": self.messages_received,
            "last_message_at": self.last_message_at,
            "source_region": self.source_region,
            "target_region": self.target_region,
        }        




