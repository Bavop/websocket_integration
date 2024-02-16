"""Example integration using DataUpdateCoordinator."""

import asyncio
from datetime import timedelta
import logging
import random
from typing import Callable

import async_timeout
import websockets
import json
from homeassistant.components.light import LightEntity
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class MyCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, host):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="My sensor",
            always_update=False,
        )
        self.rec_data = {"temperature": {"state": 0}}
        self._host = host
        self._hass = hass
        self._name = host
        self._id = host.lower()
        self.rollers = [
            Roller(f"{self._id}_1", f"{self._name} 1", self),
            Roller(f"{self._id}_2", f"{self._name} 2", self),
            Roller(f"{self._id}_3", f"{self._name} 3", self),
        ]
        asyncio.ensure_future(self._connect_websocket())

    @property
    def hub_id(self) -> str:
        """ID for dummy hub."""
        return self._id

    async def handle_websocket_message(self, message):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            self.async_set_updated_data(data)
        except Exception as e:
            pass

    async def _connect_websocket(self):
        """Establish WebSocket connection."""
        uri = "ws://192.168.5.176:5000"

        async with websockets.connect(uri) as websocket:
            await websocket.send("Hello server")
            while True:
                data = await websocket.recv()
                # self.rec_data = json.loads(await websocket.recv())
                await self.handle_websocket_message(data)

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        pass


class Roller(CoordinatorEntity):
    """Dummy roller (device for HA) for Hello World example."""

    def __init__(
        self, rollerid: str, name: str, coordinator: DataUpdateCoordinator
    ) -> None:
        super().__init__(coordinator, context="temperature")

        """Init dummy roller."""
        self._id = rollerid
        self.coordinator = coordinator
        self.name = name
        self._callbacks = set()
        self.firmware_version = f"0.0.{random.randint(1, 9)}"
        self.model = "Test Device"
        self.lux = 0

    @property
    def roller_id(self) -> str:
        """Return ID for roller."""
        return self._id

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self.lux = self.coordinator.data["temperature"]["state"]
        self.async_write_ha_state()

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when Roller changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    # In a real implementation, this library would call it's call backs when it was
    # notified of any state changeds for the relevant device.
    async def publish_updates(self) -> None:
        """Schedule call all registered callbacks."""
        self._current_position = self._target_position
        for callback in self._callbacks:
            callback()

    @property
    def online(self) -> float:
        """Roller is online."""
        # The dummy roller is offline about 10% of the time. Returns True if online,
        # False if offline.
        return random.random() > 0.1

    @property
    def illuminance(self) -> int:
        """Return a sample illuminance in lux."""
        return self.lux
