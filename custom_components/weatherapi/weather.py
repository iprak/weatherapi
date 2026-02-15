"""Support for WeatherAPI integration."""

from collections.abc import Mapping
from typing import Any

from homeassistant.components.weather import (
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_OZONE,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_VISIBILITY,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_SPEED,
    ENTITY_ID_FORMAT,
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    CONF_NAME,
    PRECISION_TENTHS,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import WeatherAPIUpdateCoordinator
from .const import (
    ATTR_REPORTED_CONDITION,
    ATTR_WEATHER_CONDITION,
    ATTRIBUTION,
    DAILY_FORECAST,
    DOMAIN,
    HOURLY_FORECAST,
)
from .coordinator import WeatherAPIConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeatherAPIConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add weather entity."""
    location_name: str = entry.data[CONF_NAME]
    async_add_entities([WeatherAPIEntity(location_name, entry.runtime_data)])


class WeatherAPIEntity(CoordinatorEntity, WeatherEntity):
    """Define a WeatherAPI entity."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.MBAR
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_precision = PRECISION_TENTHS
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY
    )

    def __init__(
        self, location_name: str, coordinator: WeatherAPIUpdateCoordinator
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self._attr_name = location_name
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, f"{DOMAIN}_{location_name}", hass=coordinator.hass
        )
        self._attr_unique_id = f"{self.coordinator.location}_{location_name}"

    @property
    def available(self) -> bool:
        """Return if weather data is available."""
        return self.coordinator.data is not None

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
    def condition(self) -> str | None:
        """Return the current condition."""
        return self.coordinator.data.get(ATTR_WEATHER_CONDITION)

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return additional specific state attributes."""
        return {
            ATTR_REPORTED_CONDITION: self.coordinator.data.get(ATTR_REPORTED_CONDITION)
        }

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        return self.coordinator.data.get(DAILY_FORECAST)

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast in native units."""
        return self.coordinator.data.get(HOURLY_FORECAST)
