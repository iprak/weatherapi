"""Support for WeatherAPI integration."""

from __future__ import annotations

from typing import Final

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UV_INDEX
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.weatherapi.const import ATTRIBUTION

from . import WeatherAPIUpdateCoordinator
from .const import ATTR_UV, DOMAIN

SENSOR_TYPE_UV: Final = "uv"
ENTITY_ID_FORMAT = SENSOR_TYPE_UV + ".{}"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add sensor device."""
    name: str = entry.data[CONF_NAME]
    coordinator: WeatherAPIUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WeatherAPIUVEntity(name, coordinator)])


class WeatherAPIUVEntity(CoordinatorEntity, SensorEntity):
    """Define an uv entity."""

    def __init__(self, name: str, coordinator: WeatherAPIUpdateCoordinator):
        """Initialize."""
        super().__init__(coordinator)

        self._name = f"{name} UV"
        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, f"{DOMAIN}_{self._name}", hass=coordinator.hass
        )
        self._unique_id = f"{self.coordinator.location}_{self._name}"
        self._attr_attribution = ATTRIBUTION
        self._attr_native_unit_of_measurement = UV_INDEX

        self.entity_description = SensorEntityDescription(
            key=SENSOR_TYPE_UV,
            name=UV_INDEX,
            icon="mdi:weather-sunny",
            native_unit_of_measurement=UV_INDEX,
            state_class=SensorStateClass.MEASUREMENT,
        )

    @property
    def available(self) -> bool:
        """Return if weather data is available."""
        return self.coordinator.data is not None

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return self.coordinator.data.get(ATTR_UV)
