"""MagicStrip number entity implementation. Use to adjust effect speed."""
from __future__ import annotations

from collections.abc import MutableMapping
import logging
from typing import Any

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pymagicstrip import MagicStripDevice
from pymagicstrip import MagicStripState

from . import async_setup_entry_platform
from . import DeviceState
from .const import DEFAULT_SPEED

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up tuya sensors dynamically through tuya discovery."""

    def _constructor(device_state: DeviceState) -> list[Entity]:
        return [
            MagicStripEffectSpeed(
                device_state.coordinator,
                device_state.device,
                device_state.effect_speed_device_info,
                device_state.light_extra_state_attributes,
            )
        ]

    async_setup_entry_platform(hass, config_entry, async_add_entities, _constructor)


class MagicStripEffectSpeed(CoordinatorEntity[MagicStripState], NumberEntity):
    """Slider for setting effect speed."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[MagicStripState],
        device: MagicStripDevice,
        device_info: DeviceInfo,
        extra_state_attributes: MutableMapping[str, Any],
    ):
        """Create for setting effect speed."""
        super().__init__(coordinator)

        self._device = device

        self._attr_mode = "slider"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 100
        self._attr_device_info = device_info
        self._attr_name = device_info["default_name"]
        self._attr_extra_state_attributes = extra_state_attributes
        self._attr_icon = "mdi:speedometer"

    @property
    def native_value(self) -> float | None:
        """Return the entity value to represent the entity state."""
        if data := self.coordinator.data:
            speed = DEFAULT_SPEED if not data.effect_speed else data.effect_speed
            rebased_speed = int((100 * speed) / 255)
            _LOGGER.debug("Retrieving speed. Stored: {speed}, Rebased: {rebased_speed}")
            return rebased_speed

        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""

        rebased_speed = int((255 * value) / 100)

        _LOGGER.debug("Setting speed. User: {value}, Rebased: {rebased_speed}")

        await self._device.set_effect_speed(int(rebased_speed))

        self.coordinator.async_set_updated_data(self._device.state)
