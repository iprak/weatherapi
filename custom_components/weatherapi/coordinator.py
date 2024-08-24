"""The WeatherAPI data coordinator."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from http import HTTPStatus
import logging
from typing import Any

import aiohttp
from aiohttp import ClientSession
import requests

from homeassistant.components.air_quality import (
    ATTR_CO,
    ATTR_NO2,
    ATTR_OZONE,
    ATTR_PM_2_5,
    ATTR_PM_10,
    ATTR_SO2,
)
from homeassistant.components.sensor import SensorEntityDescription
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
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_AIR_QUALITY_UK_DEFRA_INDEX,
    ATTR_AIR_QUALITY_US_EPA_INDEX,
    ATTR_REPORTED_CONDITION,
    ATTR_UV,
    ATTR_WEATHER_CONDITION,
    CONDITION_MAP,
    DAILY_FORECAST,
    DEFAULT_FORECAST,
    DEFAULT_IGNORE_PAST_HOUR,
    FORECAST_DAYS,
    HOURLY_FORECAST,
)

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://api.weatherapi.com/v1"
TIMEZONE_URL = f"{BASE_URL}/timezone.json"
CURRENT_URL = f"{BASE_URL}/current.json"
FORECAST_URL = f"{BASE_URL}/forecast.json"


def get_logger():
    """Get the current logger."""
    return _LOGGER


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
        async with asyncio.timeout(10):
            response = await session.get(
                TIMEZONE_URL, timeout=10, headers=headers, params=params
            )

            json_data = await response.json()

            error = json_data.get("error")
            if error:
                _LOGGER.error(
                    "WeatherAPI responded with error %s: %s",
                    error.get("code"),
                    error.get("message"),
                )
                return False

            if response.status != HTTPStatus.OK:
                _LOGGER.error(
                    "WeatherAPI responded with HTTP error %s: %s",
                    response.status,
                    response.reason,
                )
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
    forecast: bool = DEFAULT_FORECAST
    ignore_past_forecast: bool = DEFAULT_IGNORE_PAST_HOUR


class WeatherAPIUpdateCoordinator(DataUpdateCoordinator):
    """The WeatherAPI update coordinator."""

    def __init__(
        self, hass: HomeAssistant, config: WeatherAPIUpdateCoordinatorConfig
    ) -> None:
        """Initialize."""

        self._hass = hass
        self.config = config
        self._forecast_tz = None

        super().__init__(
            hass,
            _LOGGER,
            name="WeatherAPIUpdateCoordinator",
            update_interval=config.update_interval,
        )

    @property
    def location(self):
        """Return the location used for data."""
        return self.config.location

    async def _async_update_data(self) -> dict[str, Any]:
        return await self.get_weather()

    async def get_weather(self):
        """Get weather data."""

        params = {
            "key": self.config.api_key,
            "q": self.config.location,
            "days": FORECAST_DAYS,
            "aqi": "yes",
        }

        headers = {
            "accept": "application/json",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        }

        try:
            session: ClientSession = async_get_clientsession(self.hass)
            async with asyncio.timeout(10):
                response = await session.get(
                    FORECAST_URL if self.config.forecast else CURRENT_URL,
                    timeout=10,
                    headers=headers,
                    params=params,
                )

                # Deciode only if 200 status. This should avoid
                # JSONDecodeError: Expecting value: line 1 column 1 (char 0)
                if response.status != HTTPStatus.OK:
                    raise UpdateFailed(
                        f"WeatherAPI responded with status={response.status}, reason={response.reason}"
                    )

                json_data = await response.json(content_type=None)
                if json_data is None:
                    raise UpdateFailed(
                        f"WeatherAPI responded with HTTP error {response.status} but no data was provided."
                    )

                error = json_data.get("error")
                if error:
                    raise UpdateFailed(
                        f"WeatherAPI responded with error={error.get("code")}, message={error.get("message")}"
                    )

                # Using timeZome from location falling back to local timezone
                location = json_data.get("location", {})
                self.populate_time_zone(
                    location.get("tz_id", self.hass.config.time_zone)
                )

                result = self.parse_current(json_data.get("current"))
                result[DAILY_FORECAST] = (
                    self.parse_forecast(json_data.get("forecast"), False)
                    if self.config.forecast
                    else None
                )
                result[HOURLY_FORECAST] = (
                    self.parse_forecast(json_data.get("forecast"), True)
                    if self.config.forecast
                    else None
                )
                return result

        except asyncio.TimeoutError as exception:
            raise UpdateFailed(
                f"Timeout invoking WeatherAPI end point: {exception}"
            ) from exception
        except aiohttp.ClientError as exception:
            raise UpdateFailed(
                f"Error invoking WeatherAPI end point: {exception}"
            ) from exception

    def populate_time_zone(self, zone: str):
        """Define timzeone for the forecasts."""
        self._forecast_tz = dt_util.get_time_zone(zone)

    def parse_forecast(self, json, hourly_forecast: bool) -> list[Forecast]:
        """Parse the forecast JSON data."""
        entries = []

        if not json:
            _LOGGER.warning("No forecast data received")
            return entries

        _LOGGER.debug("Forecast %s=%s", self.config.name, json)

        forecastday_array = json.get("forecastday")
        if not forecastday_array:
            _LOGGER.warning("No day forecast found in data")
            return entries

        for forecastday in forecastday_array:
            # `date` is in YYYY-MM-DD format
            # `date_epoch` is unix time

            day = forecastday.get("day")

            if hourly_forecast:
                hour_array = forecastday.get("hour")
                hour_forecast_with_no_data = 0

                for hour_json in hour_array:
                    # Skip hourly forecast if it is empty .. `time` is missing

                    hour_entry_tuple = self.parse_hour_forecast(hour_json)
                    if hour_entry_tuple is None:
                        hour_forecast_with_no_data += 1
                    else:
                        hour_entry = hour_entry_tuple[1]

                        # Don't count past forcasts (if they are being ignored) in hour_forecast_with_no_data
                        if hour_entry:
                            entries.append(hour_entry)

                if hour_forecast_with_no_data > 0:
                    _LOGGER.warning(
                        "Found %d hourly forecasts for %s with no data",
                        hour_forecast_with_no_data,
                        self.config.name,
                    )

            else:
                condition = day.get("condition", {})
                is_day = to_int(day.get("is_day", "1")) == 1
                condition_code = condition.get("code")

                day_entry = Forecast(
                    condition=parse_condition_code(condition_code, is_day),
                    datetime=datetime_to_iso(forecastday.get("date")),
                    precipitation_probability=day.get("daily_chance_of_rain"),
                    native_precipitation=to_float(day.get("totalprecip_mm")),
                    # There is no pressure element
                    native_temperature=to_float(day.get("maxtemp_c")),
                    native_templow=to_float(day.get("mintemp_c")),
                    # There is no wind_dir
                    naive_wind_speed=to_float(day.get("maxwind_kph")),
                )
                day_entry[ATTR_REPORTED_CONDITION] = condition_code

                entries.append(day_entry)

        _LOGGER.info("Loaded %s forecast values for %s", len(entries), self.config.name)
        return entries

    def parse_hour_forecast(self, data: any) -> tuple[bool, Forecast]:
        """Parse hour forecast data."""

        if data is None:
            return None

        # Sometimes the hourly forecast is empty, skip if `time_epoch` element is missing.
        time_epoch = data.get("time_epoch")
        if time_epoch is None:
            return None

        now_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        now_hour_ts = now_hour.timestamp()

        if self.config.ignore_past_forecast and (time_epoch < now_hour_ts):
            _LOGGER.debug("%s: Ignoring past forecast", self.config.location)
            return [False, None]

        condition = data.get("condition", {})
        hour_forecast_time = datetime.fromtimestamp(
            time_epoch, tz=self._forecast_tz
        ).isoformat()

        is_day = to_int(data.get("is_day", "1")) == 1
        condition_code = condition.get("code")

        value = Forecast(
            condition=parse_condition_code(condition_code, is_day),
            datetime=hour_forecast_time,
            precipitation_probability=data.get("chance_of_rain"),
            native_precipitation=to_float(data.get("precip_mm")),
            native_pressure=to_float(data.get("pressure_mb")),
            native_temperature=to_float(data.get("temp_c")),
            wind_bearing=data.get("wind_dir"),
            native_wind_speed=to_float(data.get("wind_kph")),
        )
        value[ATTR_REPORTED_CONDITION] = condition_code
        return [True, value]

    def parse_current(self, json):
        """Parse the current weather JSON data."""
        if not json:
            _LOGGER.warning("No current data received")
            return {}

        _LOGGER.debug(json)

        condition = json.get("condition", {})

        air_quality = json.get("air_quality", {})
        if not air_quality:
            _LOGGER.debug("No air_quality found in data")
            air_quality = {}

        is_day = to_int(json.get("is_day", "1")) == 1
        condition_code = condition.get("code")

        return {
            ATTR_WEATHER_HUMIDITY: to_float(json.get("humidity")),
            ATTR_WEATHER_TEMPERATURE: to_float(json.get("temp_c")),
            ATTR_WEATHER_PRESSURE: to_float(json.get("pressure_mb")),
            ATTR_WEATHER_WIND_SPEED: to_float(json.get("wind_kph")),
            ATTR_WEATHER_WIND_BEARING: json.get("wind_degree"),
            ATTR_WEATHER_VISIBILITY: to_float(json.get("vis_km")),
            ATTR_UV: to_float(json.get("uv")),
            ATTR_REPORTED_CONDITION: condition_code,
            ATTR_WEATHER_CONDITION: parse_condition_code(condition_code, is_day),
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

    def generate_sensor_unique_id(self, description: SensorEntityDescription) -> str:
        """Generate unique id for a sensor."""
        name = f"{self.config.name} {description.name}"
        return f"{self.location}_{name}"


class InvalidApiKey(HomeAssistantError):
    """Error to indicate there is an invalid api key."""


class CannotConnect(requests.exceptions.ConnectionError):
    """Error to indicate we cannot connect."""
