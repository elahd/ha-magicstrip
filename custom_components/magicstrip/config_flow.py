"""Config flow for ha-magicstrip integration."""
from __future__ import annotations
import asyncio

import logging
from typing import Any

import voluptuous as vol

from homeassistant.helpers.config_entry_flow import register_discovery_flow
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from pymagicstrip import device_filter
from pymagicstrip.const import SERVICE_UUID

# from pymagicstrip import MagicStripDevice, MagicStripHub
from homeassistant.core import HomeAssistant
import async_timeout

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

CONST_WAIT_TIME = 20.0

async def _async_has_devices(hass: HomeAssistant) -> bool:
    """Return if there are devices that can be discovered."""

    event = asyncio.Event()

    def detection(device: BLEDevice, advertisement_data: AdvertisementData):
        _LOGGER.debug("Detected device: {} {}", device.address, device.rssi)
        if device_filter(device, advertisement_data):
            event.set()

    async with BleakScanner(
        detection_callback=detection, filters={"UUIDs": [str(SERVICE_UUID)]}
    ):
        
        _LOGGER.debug("Scanning for devices...")
        
        try:
            async with async_timeout.timeout(CONST_WAIT_TIME):
                await event.wait()
        except asyncio.TimeoutError:
            return False

    return True


register_discovery_flow(DOMAIN, "MagicStrip", _async_has_devices)

# class PlaceholderHub:
#     """Placeholder class to make tests pass.

#     TODO Remove this placeholder class and replace with things from your PyPI package.
#     """

#     def __init__(self, host: str) -> None:
#         """Initialize."""
#         self.host = host

#     async def authenticate(self, username: str, password: str) -> bool:
#         """Test if we can authenticate with the host."""
#         return True

# class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
#     """Handle a config flow for ha-magicstrip."""

#     VERSION = 1
    
#     _scan_task = None
#     _hub: None or MagicStripHub = None

#     async def _async_handle_device_search(self):
#         self._scanned_devices = await self._hub.discover()

#         self.hass.async_create_task(
#             self.hass.config_entries.flow.async_configure(flow_id=self.flow_id)
#         )

#     async def async_step_user(
#         self, user_input: dict[str, Any] | None = None
#     ) -> FlowResult:
#         """Discover devices."""
        
#         self._hub = MagicStripHub()
        
#         if not self._scan_task:
#             self._scan_task = self.hass.async_create_task(self._async_handle_device_search())
#             return self.async_show_progress(
#                 step_id="user",
#                 progress_action="scan_task",
#             )
        
#         return self.async_show_progress_done(next_step_id="devices")

#     async def async_step_devices(
#         self, user_input: dict[str, Any] | None = None
#     ) -> FlowResult:
#         """Handle the initial step."""
#         errors = {}
        
#         _LOGGER.debug(f"Found {self._scanned_devices}.")
        
#         if not self._scanned_devices:
#             return self.async_abort(reason="no_devices")
        
#         if user_input is None:
                
#             return self.async_show_form(
#                 step_id="devices", data_schema=self.schema, errors=errors
#             )

#         selected_device: MagicStripDevice
#         device: MagicStripDevice
#         for device in self._scanned_devices:
#             if device.address == user_input[CONF_DEVICE]:
#                 selected_device = device
#                 break

#         return self.async_create_entry(title=selected_device.address, data={"device": {"name": selected_device.name, "address": selected_device.address}})

#     @property
#     def schema(self) -> vol.Schema:
#         """Input schema for integration options."""

#         # TODO: Ignore devices that have already been added.

#         macs = []

#         for device in self._scanned_devices:
#             _LOGGER.debug(f"Formatting {device.address} for selection list.")
#             macs.append(device.address)

#         return vol.Schema(
#             {
#                 vol.Required(CONF_DEVICE): vol.In(macs)
#             }
#         )


# class CannotConnect(HomeAssistantError):
#     """Error to indicate we cannot connect."""


# class InvalidAuth(HomeAssistantError):
#     """Error to indicate there is invalid auth."""
