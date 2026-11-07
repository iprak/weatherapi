"""Support for WeatherAPI integration."""

from homeassistant.components.air_quality import (
    ATTR_CO,
    ATTR_NO2,
    ATTR_OZONE,
    ATTR_PM_2_5,
    ATTR_PM_10,
    ATTR_SO2,
)
from homeassistant.components.sensor import (
    ENTITY_ID_FORMAT,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.components.weather import (
    ATTR_WEATHER_APPARENT_TEMPERATURE,
    ATTR_WEATHER_CLOUD_COVERAGE,
    ATTR_WEATHER_DEW_POINT,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_VISIBILITY,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_GUST_SPEED,
    ATTR_WEATHER_WIND_SPEED,
)
from homeassistant.const import (
    CONF_NAME,
    DEGREE,
    PERCENTAGE,
    UV_INDEX,
    UnitOfDensity,
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfRatio,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription, async_generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import WeatherAPIUpdateCoordinator
from .const import (
    ATTR_AIR_QUALITY_UK_DEFRA_INDEX,
    ATTR_AIR_QUALITY_UK_DEFRA_INDEX_BAND,
    ATTR_AIR_QUALITY_US_EPA_INDEX,
    ATTR_CONDITION_TEXT,
    ATTR_HEAT_INDEX,
    ATTR_PRECIPITATION,
    ATTR_UV,
    ATTR_WIND_CHILL,
    ATTR_WIND_DIR,
    ATTRIBUTION,
    CONFIG_ADD_SENSORS,
    DEFAULT_ADD_SENSORS,
    DOMAIN as WEATHERAPI_DOMAIN,
)
from .coordinator import WeatherAPIConfigEntry

# https://www.weatherapi.com/docs/
SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=ATTR_CO,
        name="CO",
        device_class=SensorDeviceClass.CO,
        native_unit_of_measurement=UnitOfRatio.PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_OZONE,
        name="Ozone",
        device_class=SensorDeviceClass.OZONE,
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_NO2,
        name="NO2",
        device_class=SensorDeviceClass.NITROGEN_DIOXIDE,
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_SO2,
        name="SO2",
        device_class=SensorDeviceClass.SULPHUR_DIOXIDE,
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_PM_2_5,
        name="PM 2.5",
        icon="mdi:air-filter",
        device_class=SensorDeviceClass.PM25,
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_PM_10,
        name="PM 1.0",
        icon="mdi:air-filter",
        device_class=SensorDeviceClass.PM10,
        native_unit_of_measurement=UnitOfDensity.MICROGRAMS_PER_CUBIC_METER,
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
    SensorEntityDescription(
        key=ATTR_WEATHER_TEMPERATURE,
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_WEATHER_APPARENT_TEMPERATURE,
        name="Feels Like Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_WEATHER_DEW_POINT,
        name="Dew Point",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_WIND_CHILL,
        name="Wind Chill",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_HEAT_INDEX,
        name="Heat Index",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_WEATHER_HUMIDITY,
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_WEATHER_PRESSURE,
        name="Pressure",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        native_unit_of_measurement=UnitOfPressure.MBAR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_WEATHER_WIND_SPEED,
        name="Wind Speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_WEATHER_WIND_GUST_SPEED,
        name="Wind Gust",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_WEATHER_WIND_BEARING,
        name="Wind Bearing",
        icon="mdi:compass",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_WIND_DIR,
        name="Wind Direction",
        icon="mdi:compass-rose",
    ),
    SensorEntityDescription(
        key=ATTR_PRECIPITATION,
        name="Precipitation",
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_WEATHER_CLOUD_COVERAGE,
        name="Cloud Coverage",
        icon="mdi:weather-partly-cloudy",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_WEATHER_VISIBILITY,
        name="Visibility",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_CONDITION_TEXT,
        name="Condition",
        icon="mdi:weather-partly-cloudy",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeatherAPIConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensor devices."""

    if not entry.options.get(CONFIG_ADD_SENSORS, DEFAULT_ADD_SENSORS):
        return

    location_name: str = entry.data[CONF_NAME]
    coordinator = entry.runtime_data

    entities = [
        WeatherAPISensorEntity(location_name, coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class WeatherAPISensorEntity(CoordinatorEntity, SensorEntity):
    """Define a WeatherAPI air quality sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        location_name: str,
        coordinator: WeatherAPIUpdateCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        name = f"{location_name} {description.name}"
        self.entity_description = description

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, f"{WEATHERAPI_DOMAIN}_{name}", hass=coordinator.hass
        )

        self._attr_unique_id = coordinator.generate_sensor_unique_id(description)

    @property
    def available(self) -> bool:
        """Return if weather data is available."""
        return self.coordinator.data is not None

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
    def convert_uk_defra_index_to_band(value: int) -> str | None:
        """Convert UK DEFRA INDEX to band."""
        if value is None:
            return None
        if value >= 1:
            if value < 4:
                return "Low"
            if value < 7:
                return "Moderate"
            if value < 10:
                return "High"
            return "Very High"
        return None
