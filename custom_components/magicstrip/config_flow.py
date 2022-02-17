"""Config flow for ha-magicstrip integration."""
from __future__ import annotations

import asyncio
import logging

import async_timeout
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_flow import register_discovery_flow
from pymagicstrip import device_filter
from pymagicstrip.const import SERVICE_UUID

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
