"""The WeatherAPI integration."""

from datetime import timedelta
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

from custom_components.weatherapi.const import (
    CONFIG_FORECAST,
    CONFIG_HOURLY_FORECAST,
    DEFAULT_FORECAST,
    DEFAULT_HOURLY_FORECAST,
    DOMAIN,
    UPDATE_INTERVAL_MINUTES,
)
from custom_components.weatherapi.coordinator import (
    WeatherAPIUpdateCoordinator,
    WeatherAPIUpdateCoordinatorConfig,
)

PLATFORMS: Final = [Platform.WEATHER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the WeatherAPI component."""

    hass.data.setdefault(DOMAIN, {})

    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]

    config = WeatherAPIUpdateCoordinatorConfig(
        api_key=entry.data[CONF_API_KEY],
        location=f"{latitude},{longitude}",
        name=entry.data[CONF_NAME],
        update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        forecast=entry.options.get(CONFIG_FORECAST, DEFAULT_FORECAST),
        hourly_forecast=entry.options.get(
            CONFIG_HOURLY_FORECAST, DEFAULT_HOURLY_FORECAST
        ),
    )

    coordinator = WeatherAPIUpdateCoordinator(hass, config)
    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    hass.data[DOMAIN][entry.entry_id] = coordinator
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

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
