"""Config flow for WeatherAPI integration."""

import logging

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from custom_components.weatherapi.coordinator import CannotConnect, is_valid_api_key

from .const import (  # pylint:disable=unused-import
    CONFIG_FORECAST,
    CONFIG_HOURLY_FORECAST,
    DEFAULT_FORECAST,
    DEFAULT_HOURLY_FORECAST,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def get_data_schema(hass: HomeAssistant) -> vol.Schema:
    """Return data schema."""
    return vol.Schema(
        {
            vol.Required(CONF_API_KEY): str,
            vol.Required(CONF_NAME, default=hass.config.location_name): str,
            vol.Required(CONF_LATITUDE, default=hass.config.latitude): cv.latitude,
            vol.Required(CONF_LONGITUDE, default=hass.config.longitude): cv.longitude,
        }
    )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONFIG_FORECAST,
                    default=self.config_entry.options.get(
                        CONFIG_FORECAST,
                        DEFAULT_FORECAST,
                    ),
                ): bool,
                vol.Required(
                    CONFIG_HOURLY_FORECAST,
                    default=self.config_entry.options.get(
                        CONFIG_HOURLY_FORECAST,
                        DEFAULT_HOURLY_FORECAST,
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)


class WeatherAPIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for WeatherAPI."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            latitude = user_input[CONF_LATITUDE]
            longitude = user_input[CONF_LONGITUDE]

            await self.async_set_unique_id(f"{latitude}-{longitude}")
            self._abort_if_unique_id_configured()

            try:
                valid_key = await is_valid_api_key(self.hass, user_input[CONF_API_KEY])
                if not valid_key:
                    errors["base"] = "invalid_api_key"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=get_data_schema(self.hass),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)
