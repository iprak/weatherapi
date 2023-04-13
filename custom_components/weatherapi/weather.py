"""Support for WeatherAPI integration."""

from __future__ import annotations

from typing import Any, Mapping

from homeassistant.components.weather import (
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_OZONE,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_VISIBILITY,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_SPEED,
    DOMAIN as WEATHER_DOMAIN,
    Forecast,
    WeatherEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    LENGTH_KILOMETERS,
    LENGTH_MILES,
    PRECISION_TENTHS,
    PRESSURE_PA,
    PRESSURE_PSI,
    SPEED_KILOMETERS_PER_HOUR,
    SPEED_MILES_PER_HOUR,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.weatherapi.const import ATTRIBUTION

from . import WeatherAPIUpdateCoordinator
from .const import (
    ATTR_REPORTED_CONDITION,
    ATTR_WEATHER_CONDITION,
    DATA_FORECAST,
    DOMAIN,
)

ENTITY_ID_FORMAT = WEATHER_DOMAIN + ".{}"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add weather entity."""
    location_name: str = entry.data[CONF_NAME]
    coordinator: WeatherAPIUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WeatherAPIEntity(location_name, coordinator)])


class WeatherAPIEntity(CoordinatorEntity, WeatherEntity):
    """Define a WeatherAPI entity."""

    def __init__(self, location_name: str, coordinator: WeatherAPIUpdateCoordinator):
        """Initialize."""
        super().__init__(coordinator)

        self._name = location_name
        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, f"{DOMAIN}_{self._name}", hass=coordinator.hass
        )
        self._unique_id = f"{self.coordinator.location}_{self._name}"
        self._attr_attribution = ATTRIBUTION

        self._attr_precision = PRECISION_TENTHS

        """
        The weatherAPI documentation defines pressure data pieces as pressure_mb
        (Pressure in millibars) and pressure_in (Pressure in inches). But values
        received turn out to be in Pa and Psi.
        """

        if coordinator.is_metric:
            self._attr_native_pressure_unit = PRESSURE_PA
            self._attr_native_temperature_unit = TEMP_CELSIUS
            self._attr_native_wind_speed_unit = SPEED_KILOMETERS_PER_HOUR
            self._attr_native_visibility_unit = LENGTH_KILOMETERS
        else:
            self._attr_native_pressure_unit = PRESSURE_PSI
            self._attr_native_temperature_unit = TEMP_FAHRENHEIT
            self._attr_native_wind_speed_unit = SPEED_MILES_PER_HOUR
            self._attr_native_visibility_unit = LENGTH_MILES

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
    def native_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data.get(ATTR_WEATHER_TEMPERATURE)

    @property
    def native_pressure(self) -> float | None:
        """Return the current pressure."""
        return self.coordinator.data.get(ATTR_WEATHER_PRESSURE)

    @property
    def humidity(self) -> float | None:
        """Return the current humidity."""
        return self.coordinator.data.get(ATTR_WEATHER_HUMIDITY)

    @property
    def native_wind_speed(self) -> float | None:
        """Return the current wind speed."""
        return self.coordinator.data.get(ATTR_WEATHER_WIND_SPEED)

    @property
    def wind_bearing(self) -> float | str | None:
        """Return the current wind bearing."""
        return self.coordinator.data.get(ATTR_WEATHER_WIND_BEARING)

    @property
    def ozone(self) -> float | None:
        """Return the current ozone level."""
        return self.coordinator.data.get(ATTR_WEATHER_OZONE)

    @property
    def native_visibility(self) -> float | None:
        """Return the current visibility."""
        return self.coordinator.data.get(ATTR_WEATHER_VISIBILITY)

    @property
    def forecast(self) -> list[Forecast] | None:
        """Return the current forecast array."""
        return self.coordinator.data.get(DATA_FORECAST)

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        return self.coordinator.data.get(ATTR_WEATHER_CONDITION)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional specific state attributes."""
        return {
            ATTR_REPORTED_CONDITION: self.coordinator.data.get(ATTR_REPORTED_CONDITION)
        }
