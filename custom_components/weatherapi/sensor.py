"""Support for WeatherAPI integration."""

from __future__ import annotations

from tokenize import Number
from typing import Final

from homeassistant.components.air_quality import (
    ATTR_CO,
    ATTR_NO2,
    ATTR_OZONE,
    ATTR_PM_2_5,
    ATTR_PM_10,
    ATTR_SO2,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    CONF_NAME,
    UV_INDEX,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription, generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.weatherapi.const import ATTRIBUTION

from . import WeatherAPIUpdateCoordinator
from .const import (
    ATTR_AIR_QUALITY_UK_DEFRA_INDEX,
    ATTR_AIR_QUALITY_UK_DEFRA_INDEX_BAND,
    ATTR_AIR_QUALITY_US_EPA_INDEX,
    ATTR_UV,
    DOMAIN as WEATHERAPI_DOMAIN,
)

# https://www.weatherapi.com/docs/
SENSOR_DESCRIPTIONS: Final = (
    SensorEntityDescription(
        key=ATTR_CO,
        name="CO",
        device_class=SensorDeviceClass.CO,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_OZONE,
        name="Ozone",
        device_class=SensorDeviceClass.OZONE,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_NO2,
        name="NO2",
        device_class=SensorDeviceClass.NITROGEN_DIOXIDE,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_SO2,
        name="SO2",
        device_class=SensorDeviceClass.SULPHUR_DIOXIDE,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_PM_2_5,
        name="PM 2.5",
        icon="mdi:air-filter",
        device_class=SensorDeviceClass.PM25,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_PM_10,
        name="PM 1.0",
        icon="mdi:air-filter",
        device_class=SensorDeviceClass.PM10,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_AIR_QUALITY_US_EPA_INDEX,
        name="US - EPA",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_AIR_QUALITY_UK_DEFRA_INDEX,
        name="UK Defra Index",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_UV,
        name=UV_INDEX,
        icon="mdi:weather-sunny",
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add sensor devices."""

    location_name: str = entry.data[CONF_NAME]
    coordinator: WeatherAPIUpdateCoordinator = hass.data[WEATHERAPI_DOMAIN][
        entry.entry_id
    ]
    entities = [
        WeatherAPISensorEntity(location_name, coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class WeatherAPISensorEntity(CoordinatorEntity, SensorEntity):
    """Define a WeatherAPI air quality sensor."""

    def __init__(
        self,
        location_name: str,
        coordinator: WeatherAPIUpdateCoordinator,
        description: EntityDescription,
    ):
        """Initialize."""
        super().__init__(coordinator)

        self._name = f"{location_name} {description.name}"
        self.entity_description = description

        entity_id_format = description.key + ".{}"
        self.entity_id = generate_entity_id(
            entity_id_format, f"{WEATHERAPI_DOMAIN}_{self._name}", hass=coordinator.hass
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
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""

        self._attr_extra_state_attributes = None
        key = self.entity_description.key
        value = self.coordinator.data.get(key)

        if key == ATTR_AIR_QUALITY_UK_DEFRA_INDEX:
            band = self.convert_uk_defra_index_to_band(value)
            if band:
                self._attr_extra_state_attributes = {
                    ATTR_AIR_QUALITY_UK_DEFRA_INDEX_BAND: band
                }

        return value

    @staticmethod
    def convert_uk_defra_index_to_band(value: Number) -> str | None:
        """Convert UK DEFRA INDEX to band."""
        if value >= 1:
            if value < 4:
                return "Low"
            if value < 7:
                return "Moderate"
            if value < 10:
                return "High"
            return "Very High"
        return None
