from __future__ import annotations
from typing import Any, MutableMapping

from homeassistant.core import HomeAssistant
from homeassistant.components.light import LightEntity, COLOR_MODE_RGB, ATTR_RGB_COLOR, ATTR_BRIGHTNESS, ATTR_EFFECT, SUPPORT_EFFECT, SUPPORT_BRIGHTNESS, SUPPORT_COLOR
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed
)
from homeassistant.helpers.entity import DeviceInfo, Entity
from pymagicstrip import MagicStripDevice, MagicStripState
from pymagicstrip.errors import BleConnectionError

from .const import DEFAULT_EFFECT, DEFAULT_COLOR, DEFAULT_BRIGHTNESS
from . import DeviceState, async_setup_entry_platform

import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up tuya sensors dynamically through tuya discovery."""

    def _constructor(device_state: DeviceState) -> list[Entity]:
        return [
            MagicStripLight(
                device_state.coordinator, device_state.device, device_state.light_device_info, device_state.light_extra_state_attributes
            )
        ]

    async_setup_entry_platform(hass, config_entry, async_add_entities, _constructor)

class MagicStripLight(CoordinatorEntity[MagicStripState], LightEntity):
    def __init__(self, coordinator: DataUpdateCoordinator[MagicStripState], device: MagicStripDevice, device_info: DeviceInfo, extra_state_attributes: MutableMapping[str, Any]):
        super().__init__(coordinator)

        self._device = device
        
        self._attr_supported_color_modes = [COLOR_MODE_RGB]
        self._attr_supported_features = SUPPORT_EFFECT + SUPPORT_BRIGHTNESS + SUPPORT_COLOR
        self._attr_color_mode = COLOR_MODE_RGB
        self._attr_effect_list = self._device.state.effects_list + [DEFAULT_EFFECT]
        self._attr_unique_id = device.address
        self._attr_device_info = device_info
        self._attr_extra_state_attributes = extra_state_attributes
        self._attr_name = device_info["default_name"]
        self._attr_icon:str = "mdi:led-strip-variant"
    
    # This device doesn't return color and brighrness statuses. If we pass None to Home Assistant, it will display
    # a light without brightness, color, or effect functions. To ensure that all functions are available, we substitute
    # hard-coded values for None.
    
    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        if data := self.coordinator.data:
            return DEFAULT_EFFECT if not data.effect else data.effect
    
    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the rgb color value [int, int, int]."""
        if data := self.coordinator.data:
            return DEFAULT_COLOR if not data.color else data.color
    
    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        if data := self.coordinator.data:
            return DEFAULT_BRIGHTNESS if not data.brightness else data.brightness
    
    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        if data := self.coordinator.data:
            return data.on
        
    async def async_turn_off(self, **kwargs) -> None:
        """Turn device off."""
        
        if self.is_on:
            await self._device.toggle_power()
            
        self.coordinator.async_set_updated_data(self._device.state)
        
    async def async_turn_on(self, **kwargs) -> None:
        """Turn device on."""

        try:
            if not self.is_on:
                await self._device.toggle_power()
                        
            if ATTR_BRIGHTNESS in kwargs:
                await self._device.set_brightness(int(kwargs[ATTR_BRIGHTNESS]))
                
            if ATTR_RGB_COLOR in kwargs and (rgb_color := kwargs[ATTR_RGB_COLOR]) != self.rgb_color:
                await self._device.set_color(rgb_color[0],rgb_color[1],rgb_color[2])
                
            if ATTR_EFFECT in kwargs and (effect := kwargs[ATTR_EFFECT]) != self.effect:
                effect = None if effect == DEFAULT_EFFECT else effect
                await self._device.set_effect_name(effect)
        except BleConnectionError as exc:
            raise UpdateFailed from exc
        
        self.coordinator.async_set_updated_data(self._device.state)