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

DATA_FORECAST: Final = "forecast"

CONFIG_FORECAST: Final = "forecast"
CONFIG_HOURLY_FORECAST: Final = "hourly_forecast"

DEFAULT_FORECAST: Final = True
DEFAULT_HOURLY_FORECAST: Final = False

# https://www.weatherapi.com/docs/weather_conditions.json
CONDITION_MAP: Final[dict[str, list[int]]] = {
    ATTR_CONDITION_SUNNY: [1000],
    # ATTR_CONDITION_CLEAR_NIGHT: [1000],
    ATTR_CONDITION_PARTLYCLOUDY: [1003],
    ATTR_CONDITION_CLOUDY: [1006, 1009],
    ATTR_CONDITION_FOG: [1030, 1135, 1147],
    ATTR_CONDITION_RAINY: [1063, 1150, 1153, 1168, 1180, 1183, 1186, 1189, 1240],
    ATTR_CONDITION_HAIL: [
        1237,
    ],
    ATTR_CONDITION_LIGHTNING: [1087],
    ATTR_CONDITION_LIGHTNING_RAINY: [1273, 1276],
    ATTR_CONDITION_POURING: [1171, 1192, 1195, 1243, 1246],
    ATTR_CONDITION_SNOWY: [
        1066,
        1069,
        1114,
        1117,
        1210,
        1213,
        1216,
        1222,
        1225,
        1279,
        1282,
    ],
    ATTR_CONDITION_SNOWY_RAINY: [
        1072,
        1198,
        1201,
        1204,
        1207,
        1249,
        1252,
        1255,
        1258,
        1261,
        1264,
    ],
}
