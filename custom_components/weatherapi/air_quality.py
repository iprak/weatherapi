"""Support for WeatherAPI integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.components.air_quality import (
    ATTR_CO,
    ATTR_NO2,
    ATTR_OZONE,
    ATTR_PM_2_5,
    ATTR_PM_10,
    ATTR_SO2,
    DOMAIN as AIR_QUALITY_DOMAIN,
    AirQualityEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.weatherapi.const import ATTRIBUTION

from . import WeatherAPIUpdateCoordinator
from .const import (
    ATTR_AIR_QUALITY_UK_DEFRA_INDEX,
    ATTR_AIR_QUALITY_US_EPA_INDEX,
    DOMAIN,
)

ENTITY_ID_FORMAT = AIR_QUALITY_DOMAIN + ".{}"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add air quality entity."""
    name: str = entry.data[CONF_NAME]
    coordinator: WeatherAPIUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WeatherAPIAirQualityEntity(name, coordinator)])


class WeatherAPIAirQualityEntity(CoordinatorEntity, AirQualityEntity):
    """Define a WeatherAPI air quality entity."""

    def __init__(self, name: str, coordinator: WeatherAPIUpdateCoordinator):
        """Initialize."""
        super().__init__(coordinator)

        self._name = f"{name} Air Quality"
        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, f"{DOMAIN}_{self._name}", hass=coordinator.hass
        )
        self._unique_id = f"{self.coordinator.location}_{self._name}"
        self._attr_attribution = ATTRIBUTION

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
    def particulate_matter_2_5(self) -> StateType:
        """Return the particulate matter 2.5 level."""
        return self.coordinator.data.get(ATTR_PM_2_5)

    @property
    def particulate_matter_10(self) -> StateType:
        """Return the particulate matter 10 level."""
        return self.coordinator.data.get(ATTR_PM_10)

    @property
    def ozone(self) -> StateType:
        """Return the O3 (ozone) level."""
        return self.coordinator.data.get(ATTR_OZONE)

    @property
    def carbon_monoxide(self) -> StateType:
        """Return the CO (carbon monoxide) level."""
        return self.coordinator.data.get(ATTR_CO)

    @property
    def sulphur_dioxide(self) -> StateType:
        """Return the SO2 (sulphur dioxide) level."""
        return self.coordinator.data.get(ATTR_SO2)

    @property
    def nitrogen_dioxide(self) -> StateType:
        """Return the NO2 (nitrogen dioxide) level."""
        return self.coordinator.data.get(ATTR_NO2)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""
        return {
            ATTR_AIR_QUALITY_US_EPA_INDEX: self.coordinator.data.get(
                ATTR_AIR_QUALITY_US_EPA_INDEX
            ),
            ATTR_AIR_QUALITY_UK_DEFRA_INDEX: self.coordinator.data.get(
                ATTR_AIR_QUALITY_UK_DEFRA_INDEX
            ),
        }
