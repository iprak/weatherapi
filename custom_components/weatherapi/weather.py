"""Support for the AccuWeather service."""

import logging
from typing import Union

from homeassistant.components.weather import (
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_OZONE,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_VISIBILITY,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_SPEED,
    DOMAIN as WEATHER_DOMAIN,
    PLATFORM_SCHEMA,
    Forecast,
    WeatherEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    PRECISION_TENTHS,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import DeviceInfo, generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import voluptuous as vol

from . import WeatherAPIUpdateCoordinator
from .const import ATTR_WEATHER_CONDITION, DATA_FORECAST, DOMAIN, MANUFACTURER

ATTRIBUTION = "Powered by WeatherAPI.com"
_LOGGER = logging.getLogger(__name__)
ENTITY_ID_FORMAT = WEATHER_DOMAIN + ".{}"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
    }
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add a WeatherAPI from a config_entry."""
    name: str = entry.data[CONF_NAME]
    coordinator: WeatherAPIUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WeatherAPIEntity(name, entry.entry_id, coordinator)])


class WeatherAPIEntity(CoordinatorEntity, WeatherEntity):
    """Define a WeatherAPI entity."""

    def __init__(
        self, name: str, entry_id: str, coordinator: WeatherAPIUpdateCoordinator
    ):
        """Initialize."""
        super().__init__(coordinator)

        self.entity_id = generate_entity_id(
            ENTITY_ID_FORMAT, f"{DOMAIN}_{name}", hass=coordinator.hass
        )

        self._name = name
        self._unique_id = f"{entry_id}_{self.coordinator.location}"
        self._attr_temperature_unit = (
            TEMP_CELSIUS if self.coordinator.is_metric else TEMP_FAHRENHEIT
        )
        self._attr_precision = PRECISION_TENTHS
        self._attr_attribution = ATTRIBUTION

    @property
    def available(self) -> bool:
        """Return if weather data is available."""
        return self.coordinator.data is not None

    @property
    def device_info(self) -> Union[DeviceInfo, None]:
        """Return device information about the application."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._unique_id)},
            name=self._name,
            manufacturer=MANUFACTURER,
            entry_type="service",
        )

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def temperature(self) -> Union[float, None]:
        """Return the temperature."""
        return self.coordinator.data.get(ATTR_WEATHER_TEMPERATURE)

    @property
    def pressure(self) -> Union[float, None]:
        """Return the pressure."""
        return self.coordinator.data.get(ATTR_WEATHER_PRESSURE)

    @property
    def humidity(self) -> Union[float, None]:
        """Return the humidity."""
        return self.coordinator.data.get(ATTR_WEATHER_HUMIDITY)

    @property
    def wind_speed(self) -> Union[float, None]:
        """Return the wind speed."""
        return self.coordinator.data.get(ATTR_WEATHER_WIND_SPEED)

    @property
    def wind_bearing(self) -> Union[float, str, None]:
        """Return the wind bearing."""
        return self.coordinator.data.get(ATTR_WEATHER_WIND_BEARING)

    @property
    def ozone(self) -> Union[float, None]:
        """Return the ozone level."""
        return self.coordinator.data.get(ATTR_WEATHER_OZONE)

    @property
    def visibility(self) -> Union[float, None]:
        """Return the visibility."""
        return self.coordinator.data.get(ATTR_WEATHER_VISIBILITY)

    @property
    def forecast(self) -> Union[list[Forecast], None]:
        """Return the forecast array."""
        return self.coordinator.data.get(DATA_FORECAST)

    @property
    def condition(self) -> Union[str, None]:
        """Return the current condition."""
        return self.coordinator.data.get(ATTR_WEATHER_CONDITION)
