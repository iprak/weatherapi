"""The WeatherAPI data coordinator."""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any, cast

import aiohttp
from aiohttp import ClientSession
import async_timeout
from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_SUNNY,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_SPEED,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_OZONE,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_VISIBILITY,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_SPEED,
)
from homeassistant.const import HTTP_OK
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import homeassistant.util.dt as dt_util
import requests

from custom_components.weatherapi.const import (
    ATTR_WEATHER_CONDITION,
    CONDITION_MAP,
    DATA_FORECAST,
    FORECAST_DAYS,
)

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.weatherapi.com/v1"
TIMEZONE_URL = f"{BASE_URL}/timezone.json"
CURRENT_URL = f"{BASE_URL}/current.json"
FORECAST_URL = f"{BASE_URL}/forecast.json"


def to_float(value):
    """Safely convert string value to rounded float."""
    if value is None:
        return None

    try:
        return round(
            float(value),
            1,
        )
    except (ValueError, TypeError):
        return None


def to_int(value):
    """Safely convert string value to int."""
    if value is None:
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_condition_code(value, is_day: bool = True) -> str:
    """Convert WeatherAPI condition code to standard weather condition."""
    if value is None:
        return None

    try:
        condition_code = int(value)

        if condition_code == 1000:
            return ATTR_CONDITION_SUNNY if is_day else ATTR_CONDITION_CLEAR_NIGHT

        matches = [k for k, v in CONDITION_MAP.items() if condition_code in v]
        condition = matches[0]
    except:  # noqa: E722 pylint: disable=bare-except
        condition = None

    return condition


async def is_valid_api_key(hass: HomeAssistant, api_key: str) -> bool:
    """Check if the api_key is valid."""

    if api_key is None or api_key == "":
        raise InvalidApiKey

    params = {"key": api_key, "q": "00501"}  # Using NewYork for key check
    headers = {
        "accept": "application/json",
        "user-agent": "APIMATIC 2.0",
    }

    try:
        session: ClientSession = async_get_clientsession(hass)
        with async_timeout.timeout(10):
            response = await session.get(
                TIMEZONE_URL, timeout=10, headers=headers, params=params
            )

            if response.status != HTTP_OK:
                _LOGGER.error("Timeout connecting to WeatherAPI end point")
                return False

            json = await response.json()

            error = json.get("error")
            if error is None:
                return True

            if error.get("code"):
                return False

            return True

    except (asyncio.TimeoutError, aiohttp.ClientError) as exception:
        _LOGGER.error("Timeout calling WeatherAPI end point: %s", exception)
        raise CannotConnect from exception


@dataclass
class WeatherAPIUpdateCoordinatorConfig:
    """Class representing coordinator configuration."""

    api_key: str
    location: str
    name: str
    update_interval: timedelta
    forecast: bool = True


class WeatherAPIUpdateCoordinator(DataUpdateCoordinator):
    """The WeatherAPI update coordinator."""

    def __init__(
        self, hass: HomeAssistant, config: WeatherAPIUpdateCoordinatorConfig
    ) -> None:
        """Initialize."""

        self._api_key = config.api_key
        self._location = config.location
        self._forecast = config.forecast
        self._name = config.name

        self._is_metric = hass.config.units.is_metric

        super().__init__(
            hass,
            _LOGGER,
            name="WeatherAPIUpdateCoordinator",
            update_interval=config.update_interval,
        )

    @property
    def is_metric(self):
        """Determine if this is the metric unit system."""
        return self._is_metric

    @property
    def location(self):
        """Return the location used for data."""
        return self._location

    async def _async_update_data(self) -> dict[str, Any]:
        return await self.get_weather()

    async def get_weather(self):
        """Get weather forecast."""

        params = {
            "key": self._api_key,
            "q": self._location,
            "days": FORECAST_DAYS,
            "aqi": "yes",
        }
        headers = {
            "accept": "application/json",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/34.0.1847.116 Chrome/34.0.1847.116 Safari/537.36",
        }

        try:
            session: ClientSession = async_get_clientsession(self.hass)
            with async_timeout.timeout(10):
                response = await session.get(
                    FORECAST_URL if self._forecast else CURRENT_URL,
                    timeout=10,
                    headers=headers,
                    params=params,
                )

                if response.status != HTTP_OK:
                    _LOGGER.error("Timeout connecting to WeatherAPI end point")
                    return

                json_data = await response.json()
                result = self.parse_current(json_data.get("current"))
                result[DATA_FORECAST] = self.parse_forecast(json_data.get("forecast"))
                return result

        except (asyncio.TimeoutError, aiohttp.ClientError) as exception:
            _LOGGER.error("Timeout calling WeatherAPI end point: %s", exception)
            raise CannotConnect from exception

    def parse_forecast(self, json):
        """Parse the forcast JSON data."""
        entries = []

        if not json:
            _LOGGER.warning("No data received.")
            return entries

        _LOGGER.debug(json)

        forecastday = json.get("forecastday")
        if not forecastday:
            _LOGGER.warning("No forecast found in data.")
            return entries

        is_metric = self._is_metric

        for forecastday_entry in forecastday:
            # `date` is in YYYY-MM-DD format
            # `date_epoch` is unix time

            forecast_date = dt_util.as_utc(
                dt_util.parse_datetime(forecastday_entry.get("date"))
            )

            forecast_data = forecastday_entry.get("day")
            forecast_condition = forecast_data.get("condition")

            entry = {
                ATTR_FORECAST_TIME: forecast_date.isoformat(),
                ATTR_FORECAST_TEMP: to_float(
                    forecast_data.get("maxtemp_c" if is_metric else "maxtemp_f")
                ),
                ATTR_FORECAST_TEMP_LOW: to_float(
                    forecast_data.get("mintemp_c" if is_metric else "mintemp_f")
                ),
                ATTR_FORECAST_PRECIPITATION: to_float(
                    forecast_data.get(
                        "totalprecip_mm" if is_metric else "totalprecip_in"
                    )
                ),
                ATTR_FORECAST_PRECIPITATION_PROBABILITY: forecast_data.get(
                    "daily_chance_of_rain"
                ),
                ATTR_FORECAST_WIND_SPEED: to_float(
                    forecast_data.get("maxwind_kph" if is_metric else "maxwind_mph")
                ),
                ATTR_FORECAST_CONDITION: parse_condition_code(
                    forecast_condition.get("code")
                )
                if forecast_condition
                else None,
            }

            entries.append(entry)

        _LOGGER.info("Loaded %s days of forecast for %s.", len(entries), self._name)
        return entries

    def parse_current(self, json):
        """Parse the current JSON data."""
        if not json:
            _LOGGER.warning("No current data received.")
            return {}

        _LOGGER.debug(json)

        is_metric = self._is_metric
        condition = json.get("condition")
        air_quality = json.get("air_quality")
        is_day = to_int(json.get("is_day")) == 1

        return {
            ATTR_WEATHER_HUMIDITY: to_float(json.get("humidity")),
            ATTR_WEATHER_TEMPERATURE: to_float(
                json.get(("temp_c" if is_metric else "temp_f"))
            ),
            ATTR_WEATHER_PRESSURE: to_float(
                json.get(("precip_mm" if is_metric else "precip_in"))
            ),
            ATTR_WEATHER_WIND_SPEED: to_float(
                json.get(("wind_kph" if is_metric else "wind_mph"))
            ),
            ATTR_WEATHER_WIND_BEARING: json.get("wind_degree"),
            ATTR_WEATHER_VISIBILITY: to_float(
                json.get("vis_km" if is_metric else "vis_miles")
            ),
            ATTR_WEATHER_CONDITION: parse_condition_code(condition.get("code"), is_day)
            if condition
            else None,
            ATTR_WEATHER_OZONE: to_float(air_quality.get("o3"))
            if air_quality
            else None,
        }


class InvalidApiKey(HomeAssistantError):
    """Error to indicate there is an invalid api key."""


class CannotConnect(requests.exceptions.ConnectionError):
    """Error to indicate we cannot connect."""
