"""The WeatherAPI integration."""

from datetime import timedelta
from typing import Final

from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import (
    CONFIG_ADD_SENSORS,
    CONFIG_FORECAST,
    CONFIG_IGNORE_PAST_HOUR,
    DEFAULT_ADD_SENSORS,
    DEFAULT_FORECAST,
    DEFAULT_IGNORE_PAST_HOUR,
    DOMAIN,
    LOGGER,
    UPDATE_INTERVAL_MINUTES,
)
from .coordinator import (
    WeatherAPIConfigEntry,
    WeatherAPIUpdateCoordinator,
    WeatherAPIUpdateCoordinatorConfig,
)
from .sensor import SENSOR_DESCRIPTIONS

PLATFORMS: Final = [Platform.SENSOR, Platform.WEATHER]


async def async_setup_entry(hass: HomeAssistant, entry: WeatherAPIConfigEntry):
    """Set up the WeatherAPI component."""

    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]
    location_name = entry.data[CONF_NAME]

    config = WeatherAPIUpdateCoordinatorConfig(
        api_key=entry.data[CONF_API_KEY],
        location=f"{latitude},{longitude}",
        name=location_name,
        update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        forecast=entry.options.get(CONFIG_FORECAST, DEFAULT_FORECAST),
        ignore_past_forecast=entry.options.get(
            CONFIG_IGNORE_PAST_HOUR, DEFAULT_IGNORE_PAST_HOUR
        ),
    )

    coordinator = WeatherAPIUpdateCoordinator(hass, config, entry)
    entry.runtime_data = coordinator
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Remove previous sensor entries if sensors are not being added
    if not entry.options.get(CONFIG_ADD_SENSORS, DEFAULT_ADD_SENSORS):
        ent_reg = er.async_get(hass)

        for description in SENSOR_DESCRIPTIONS:
            unique_id = coordinator.generate_sensor_unique_id(description)

            if entity_id := ent_reg.async_get_entity_id(
                Platform.SENSOR, DOMAIN, unique_id
            ):
                LOGGER.debug("Removing sensor entity %s", entity_id)
                ent_reg.async_remove(entity_id)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: WeatherAPIConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
