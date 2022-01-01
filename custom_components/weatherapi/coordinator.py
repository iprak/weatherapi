"""The WeatherAPI data coordinator."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from http import HTTPStatus
import logging
from typing import Any

import aiohttp
from aiohttp import ClientSession
import async_timeout
from homeassistant.components.air_quality import (
    ATTR_CO,
    ATTR_NO2,
    ATTR_OZONE,
    ATTR_PM_2_5,
    ATTR_PM_10,
    ATTR_SO2,
)
from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_SUNNY,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_OZONE,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_VISIBILITY,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_SPEED,
    Forecast,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import homeassistant.util.dt as dt_util
import requests

from custom_components.weatherapi.const import (
    ATTR_AIR_QUALITY_UK_DEFRA_INDEX,
    ATTR_AIR_QUALITY_US_EPA_INDEX,
    ATTR_UV,
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


def to_float(value: str | None) -> float | None:
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


def to_int(value: str | None) -> int | None:
    """Safely convert string value to int."""
    if value is None:
        return None

    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def datetime_to_iso(value: str | None) -> str:
    """Convert date time value to iso."""

    if value is None:
        return None

    return dt_util.as_utc(dt_util.parse_datetime(value)).isoformat()


def parse_condition_code(value, is_day: bool) -> str:
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

            if response.status != HTTPStatus.OK:
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
    hourly_forecast: bool = False


class WeatherAPIUpdateCoordinator(DataUpdateCoordinator):
    """The WeatherAPI update coordinator."""

    def __init__(
        self, hass: HomeAssistant, config: WeatherAPIUpdateCoordinatorConfig
    ) -> None:
        """Initialize."""

        self._api_key = config.api_key
        self._location = config.location
        self._forecast = config.forecast
        self._hourly_forecast = config.hourly_forecast
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
        """Get weather data."""

        params = {
            "key": self._api_key,
            "q": self._location,
            "days": FORECAST_DAYS,
            "aqi": "yes",
        }

        # pylint: disable=line-too-long
        headers = {
            "accept": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
        }
        # pylint: enable=line-too-long

        try:
            session: ClientSession = async_get_clientsession(self.hass)
            with async_timeout.timeout(10):
                response = await session.get(
                    FORECAST_URL if self._forecast else CURRENT_URL,
                    timeout=10,
                    headers=headers,
                    params=params,
                )

                if response.status != HTTPStatus.OK:
                    _LOGGER.error("Timeout connecting to WeatherAPI end point")
                    return

                json_data = await response.json()
                result = self.parse_current(json_data.get("current"))
                result[DATA_FORECAST] = (
                    self.parse_forecast(json_data.get("forecast"))
                    if self._forecast
                    else None
                )
                return result

        except (asyncio.TimeoutError, aiohttp.ClientError) as exception:
            _LOGGER.error("Timeout calling WeatherAPI end point: %s", exception)
            raise CannotConnect from exception

    def parse_forecast(self, json):
        """Parse the forecast JSON data."""
        entries = []

        if not json:
            _LOGGER.warning("No forecast data received.")
            return entries

        _LOGGER.debug(json)

        forecastday_array = json.get("forecastday")
        if not forecastday_array:
            _LOGGER.warning("No day forecast found in data.")
            return entries

        is_metric = self._is_metric

        for forecastday in forecastday_array:
            # `date` is in YYYY-MM-DD format
            # `date_epoch` is unix time

            day = forecastday.get("day")

            if self._hourly_forecast:
                hour_array = forecastday.get("hour")
                hour_forecast_with_no_data = 0

                for hour in hour_array:
                    # Skip hourly forecast if it is empty .. `time` is missing

                    hour_entry = self.parse_hour_forecast(hour, is_metric)
                    if hour_entry is None:
                        hour_forecast_with_no_data += 1
                    else:
                        entries.append(hour_entry)

                if hour_forecast_with_no_data > 0:
                    _LOGGER.warning(
                        "%d hourly forecasts found for %s with no data.",
                        hour_forecast_with_no_data,
                        self._name,
                    )

            else:
                condition = day.get("condition", {})
                is_day = to_int(day.get("is_day", "1")) == 1

                day_entry = Forecast(
                    datetime=datetime_to_iso(forecastday.get("date")),
                    temperature=to_float(
                        day.get("maxtemp_c" if is_metric else "maxtemp_f")
                    ),
                    templow=to_float(
                        day.get("mintemp_c" if is_metric else "mintemp_f")
                    ),
                    precipitation=to_float(
                        day.get("totalprecip_mm" if is_metric else "totalprecip_in")
                    ),
                    precipitation_probability=day.get("daily_chance_of_rain"),
                    wind_speed=to_float(
                        day.get("maxwind_kph" if is_metric else "maxwind_mph")
                    ),
                    condition=parse_condition_code(condition.get("code"), is_day),
                )

                entries.append(day_entry)

        _LOGGER.info("Loaded %s forecast values for %s.", len(entries), self._name)
        return entries

    @staticmethod
    def parse_hour_forecast(data: any, is_metric: bool) -> Forecast:
        """Parse hour forecast data."""

        if data is None:
            return None

        # Sometimes the hourly forecast just has empty condition, skip if `time` element is missing.
        hour_forecast_time = data.get("time")
        if hour_forecast_time is None:
            return None

        condition = data.get("condition", {})
        hour_forecast_time = datetime_to_iso(hour_forecast_time)
        is_day = to_int(data.get("is_day", "1")) == 1
        return Forecast(
            datetime=hour_forecast_time,
            temperature=to_float(data.get("temp_c" if is_metric else "temp_f")),
            precipitation_probability=data.get("chance_of_rain"),
            wind_speed=to_float(data.get("wind_mph" if is_metric else "wind_kph")),
            condition=parse_condition_code(condition.get("code"), is_day),
        )

    def parse_current(self, json):
        """Parse the current weather JSON data."""
        if not json:
            _LOGGER.warning("No current data received.")
            return {}

        _LOGGER.debug(json)

        is_metric = self._is_metric
        condition = json.get("condition", {})
        air_quality = json.get("air_quality", {})
        is_day = to_int(json.get("is_day", "1")) == 1

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
            ATTR_UV: to_float(json.get("uv")),
            ATTR_WEATHER_CONDITION: parse_condition_code(condition.get("code"), is_day),
            ATTR_WEATHER_OZONE: to_float(air_quality.get("o3")),
            # Air quality data pieces
            ATTR_CO: to_float(air_quality.get("co")),
            ATTR_NO2: to_float(air_quality.get("no2")),
            ATTR_OZONE: to_float(air_quality.get("o3")),
            ATTR_PM_10: to_float(air_quality.get("so2")),
            ATTR_PM_2_5: to_float(air_quality.get("pm2_5")),
            ATTR_SO2: to_float(air_quality.get("pm10")),
            ATTR_AIR_QUALITY_UK_DEFRA_INDEX: to_int(
                air_quality.get(ATTR_AIR_QUALITY_UK_DEFRA_INDEX)
            ),
            ATTR_AIR_QUALITY_US_EPA_INDEX: to_int(
                air_quality.get(ATTR_AIR_QUALITY_US_EPA_INDEX)
            ),
        }


class InvalidApiKey(HomeAssistantError):
    """Error to indicate there is an invalid api key."""


class CannotConnect(requests.exceptions.ConnectionError):
    """Error to indicate we cannot connect."""
