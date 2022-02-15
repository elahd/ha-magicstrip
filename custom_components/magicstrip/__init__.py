"""The ha-magicstrip integration."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Callable, MutableMapping

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, ConfigEntryNotReady
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)

from pymagicstrip import MagicStripDevice, MagicStripState, device_filter
from pymagicstrip.const import SERVICE_UUID
from pymagicstrip.errors import BleTimeoutError, BleConnectionError

from .const import DOMAIN, DISPATCH_DETECTION

import asyncio

import logging

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.LIGHT]

@dataclass
class DeviceState:
    """Store state of a device."""

    device: MagicStripDevice
    coordinator: DataUpdateCoordinator[MagicStripState]
    device_info: DeviceInfo
    extra_state_attributes: MutableMapping[str, Any]


@dataclass
class EntryState:
    """Store state of config entry."""

    scanner: BleakScanner
    devices: dict[str, DeviceState]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ha-magicstrip from a config entry."""
    
    scanner = BleakScanner(filters={"UUIDs": [str(SERVICE_UUID)]})

    state = EntryState(scanner, {})
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = state

    async def detection_callback(
        ble_device: BLEDevice, advertisement_data: AdvertisementData
    ) -> None:
        if data := state.devices.get(ble_device.address):
            _LOGGER.debug(
                "Update: %s %s - %s", ble_device.name, ble_device, advertisement_data
            )

            await data.device.detection_callback(ble_device, advertisement_data)
            data.coordinator.async_set_updated_data(data.device.state)
        else:
            if not device_filter(ble_device, advertisement_data):
                return

            _LOGGER.debug(
                "Detected: %s %s - %s", ble_device.name, ble_device, advertisement_data
            )

            device = MagicStripDevice(ble_device)
            
            try:
                await device.detection_callback(ble_device, advertisement_data)
            except (BleTimeoutError, UpdateFailed) as exc:
                _LOGGER.error("Timed out when connecting to device. Will try again later. Error: %s", exc)

            async def async_update_data():
                """Handle an explicit update request."""
                try:
                    _LOGGER.debug("Updating data...")
                    await device.update()
                    _LOGGER.debug("Updated data: %s", device.state)
                except (asyncio.TimeoutError, BleTimeoutError, asyncio.exceptions.TimeoutError) as exc:
                    raise UpdateFailed(f"Timeout communicating with device: {exc}") from exc
                return device.state

            coordinator: DataUpdateCoordinator[MagicStripState] = DataUpdateCoordinator(
                hass,
                logger=_LOGGER,
                name="MagicStrip Updater",
                update_interval=timedelta(seconds=120),
                update_method=async_update_data,
            )
            
            coordinator.async_set_updated_data(device.state)

            device_info = DeviceInfo(
                identifiers={(DOMAIN, ble_device.address)},
                default_name=f"MagicStrip LED ({ble_device.address})",
            )
            
            extra_state_attributes: MutableMapping[str, Any] = {
                "integration": DOMAIN,
                "signal_strength": device.state.connection_quality
            }
            
            device_state = DeviceState(device, coordinator, device_info, extra_state_attributes)
            state.devices[ble_device.address] = device_state
            async_dispatcher_send(
                hass, f"{DISPATCH_DETECTION}.{entry.entry_id}", device_state
            )

    scanner.register_detection_callback(detection_callback)
    await scanner.start()

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

@callback
def async_setup_entry_platform(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    constructor: Callable[[DeviceState], list[Entity]],
) -> None:
    """Set up a platform with added entities."""

    entry_state: EntryState = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        entity
        for device_state in entry_state.devices.values()
        for entity in constructor(device_state)
    )

    @callback
    def _detection(device_state: DeviceState) -> None:
        async_add_entities(constructor(device_state))

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, f"{DISPATCH_DETECTION}.{entry.entry_id}", _detection
        )
    )