"""The WeatherAPI integration."""

from datetime import timedelta
import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
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
    UPDATE_INTERVAL_MINUTES,
)
from .coordinator import WeatherAPIUpdateCoordinator, WeatherAPIUpdateCoordinatorConfig
from .sensor import SENSOR_DESCRIPTIONS

PLATFORMS: Final = [Platform.WEATHER, Platform.SENSOR]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the WeatherAPI component."""

    hass.data.setdefault(DOMAIN, {})

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

    coordinator = WeatherAPIUpdateCoordinator(hass, config)
    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Remove previous sensor entries if sensors are not being added
    if not entry.options.get(CONFIG_ADD_SENSORS, DEFAULT_ADD_SENSORS):
        ent_reg = er.async_get(hass)

        for description in SENSOR_DESCRIPTIONS:
            unique_id = coordinator.generate_sensor_unique_id(description)

            if entity_id := ent_reg.async_get_entity_id(
                Platform.SENSOR, DOMAIN, unique_id
            ):
                _LOGGER.debug("Removing sensor entity %s", entity_id)
                ent_reg.async_remove(entity_id)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)
