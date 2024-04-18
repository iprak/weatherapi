"""Constants for the Weather API component."""

from typing import Final

from homeassistant.components.weather import (
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
)

DOMAIN: Final = "weatherapi"
FORECAST_DAYS: Final = 5
ATTRIBUTION: Final = "Powered by WeatherAPI.com"

# 1,000,000/month = 32,358/day = 1,344/hour = 22/minute
UPDATE_INTERVAL_MINUTES: Final = 5

ATTR_WEATHER_CONDITION: Final = "condition"
ATTR_UV: Final = "uv"
# https://www.weatherapi.com/docs/#intro-aqi
ATTR_AIR_QUALITY_US_EPA_INDEX: Final = "us-epa-index"
ATTR_AIR_QUALITY_UK_DEFRA_INDEX: Final = "gb-defra-index"
ATTR_AIR_QUALITY_UK_DEFRA_INDEX_BAND: Final = "band"
ATTR_REPORTED_CONDITION: Final = "reported_condition"

DAILY_FORECAST: Final = "daily_forecast"
HOURLY_FORECAST: Final = "hourly_forecast"

CONFIG_ADD_SENSORS: Final = "add_sensors"
CONFIG_FORECAST: Final = "forecast"
CONFIG_IGNORE_PAST_HOUR: Final = "ignore_past_hour"

DEFAULT_ADD_SENSORS: Final = True
DEFAULT_FORECAST: Final = True
DEFAULT_HOURLY_FORECAST: Final = False
DEFAULT_IGNORE_PAST_HOUR: Final = True


# https://www.weatherapi.com/docs/weather_conditions.json
CONDITION_MAP: Final[dict[str, list[int]]] = {
    # ATTR_CONDITION_CLEAR_NIGHT: [1000],
    ATTR_CONDITION_CLOUDY: [1006, 1009],  # Cloudy, Overcast
    # ATTR_CONDITION_EXCEPTIONAL
    ATTR_CONDITION_FOG: [1030, 1135, 1147],  # Mist, Fog, Freezing fog
    ATTR_CONDITION_HAIL: [
        1237,  # Ice pellets
        1261,  # Light showers of ice pellets
        1264,  # Moderate or heavy showers of ice pellets
    ],
    ATTR_CONDITION_LIGHTNING: [1087],  # Thundery outbreaks possible
    ATTR_CONDITION_LIGHTNING_RAINY: [
        1273,  # Patchy light rain with thunder
        1276,  # Moderate or heavy rain with thunder
    ],
    ATTR_CONDITION_PARTLYCLOUDY: [1003],
    ATTR_CONDITION_POURING: [
        1192,  # Heavy rain at times
        1195,  # Heavy rain
        1243,  # Moderate or heavy rain shower
        1246,  # Torrential rain shower
    ],
    ATTR_CONDITION_RAINY: [
        1063,  # Patchy rain possible
        1150,  # Patchy light drizzle
        1153,  # Light drizzle
        1180,  # Patchy light rain
        1183,  # Light rain
        1186,  # Moderate rain at times
        1189,  # Moderate rain
        1240,  # Light rain shower
    ],
    ATTR_CONDITION_SNOWY: [
        1066,  # Patchy snow possible
        1114,  # Blowing snow
        1117,  # Blizzard
        1210,  # Patchy light snow
        1213,  # Light snow
        1216,  # Patchy moderate snow
        1219,  # Moderate snow
        1222,  # Patchy heavy snow
        1225,  # Heavy snow
        1279,  # Patchy light snow with thunder
        1282,  # Moderate or heavy snow with thunder
    ],
    ATTR_CONDITION_SNOWY_RAINY: [
        1069,  # Patchy sleet possible
        1072,  # Patchy freezing drizzle possible
        1168,  # Freezing drizzle
        1171,  # Heavy freezing drizzle
        1198,  # Light freezing rain
        1201,  # Moderate or heavy freezing rain
        1204,  # Light sleet
        1207,  # Moderate or heavy sleet
        1249,  # Light sleet showers
        1252,  # Moderate or heavy sleet showers
        1255,  # Light snow showers
        1258,  # Moderate or heavy snow showers
    ],
    ATTR_CONDITION_SUNNY: [1000],  # Sunny
    # ATTR_CONDITION_WINDY
    # ATTR_CONDITION_WINDY_VARIANT
}
