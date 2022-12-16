"""Config flow for ha-magicstrip integration."""
from __future__ import annotations

import asyncio
import logging

from bleak.backends.scanner import AdvertisementData
from bleak_retry_connector import BLEDevice
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.config_entry_flow import register_discovery_flow
from pymagicstrip import device_filter
from pymagicstrip.const import SERVICE_UUID

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

CONST_WAIT_TIME = 20.0


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore
    """Handle a config flow for Yale Access Bluetooth."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self.context["local_name"] = discovery_info.name
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {
            "name": f"MagicStrip LED ({discovery_info.address})",
        }
        return await self.async_step_user()


async def _async_has_devices(hass: HomeAssistant) -> bool:
    """Return if there are devices that can be discovered."""

    event = asyncio.Event()

    def detection(device: BLEDevice, advertisement_data: AdvertisementData) -> None:
        _LOGGER.debug("Detected device: {} {}", device.address, device.rssi)
        if device_filter(device, advertisement_data):
            event.set()

    scanner = bluetooth.async_get_scanner(hass)

    await scanner.discover(
        detection_callback=detection, filters={"UUIDs": [str(SERVICE_UUID)]}
    )

    return True


register_discovery_flow(DOMAIN, "MagicStrip", _async_has_devices)
