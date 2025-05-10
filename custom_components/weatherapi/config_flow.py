"""Config flow for WeatherAPI integration."""

from http import HTTPStatus

import aiohttp
import requests
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import (
    CONFIG_ADD_SENSORS,
    CONFIG_FORECAST,
    CONFIG_IGNORE_PAST_HOUR,
    DEFAULT_ADD_SENSORS,
    DEFAULT_FORECAST,
    DEFAULT_IGNORE_PAST_HOUR,
    DOMAIN,
    LOGGER,
    TIMEZONE_URL,
)
from .coordinator import WeatherAPIConfigEntry


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


class OptionsFlowHandler(OptionsFlow):
    """Handle options flow."""

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONFIG_ADD_SENSORS,
                    default=self.config_entry.options.get(
                        CONFIG_ADD_SENSORS,
                        DEFAULT_ADD_SENSORS,
                    ),
                ): bool,
                vol.Required(
                    CONFIG_FORECAST,
                    default=self.config_entry.options.get(
                        CONFIG_FORECAST,
                        DEFAULT_FORECAST,
                    ),
                ): bool,
                vol.Required(
                    CONFIG_IGNORE_PAST_HOUR,
                    default=self.config_entry.options.get(
                        CONFIG_IGNORE_PAST_HOUR,
                        DEFAULT_IGNORE_PAST_HOUR,
                    ),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)


class WeatherAPIConfigFlow(ConfigFlow, domain=DOMAIN):
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
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected exception")
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
        config_entry: WeatherAPIConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


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
        session: aiohttp.ClientSession = async_get_clientsession(hass)

        response = await session.get(
            TIMEZONE_URL,
            timeout=aiohttp.ClientTimeout(total=10),
            headers=headers,
            params=params,
        )

        if response.status != HTTPStatus.OK:
            LOGGER.error(
                "WeatherAPI responded with HTTP error status=%s", response.status
            )
            return False

        json_data = await response.json()

        error = json_data.get("error")
        if error:
            LOGGER.error(
                "WeatherAPI responded with error %s: %s",
                error.get("code"),
                error.get("message"),
            )
            return False

    except TimeoutError as exception:
        LOGGER.error("Timeout invoking WeatherAPI end point: %s", exception)
        raise CannotConnect from exception

    except aiohttp.ClientError as exception:
        LOGGER.error("Error invoking WeatherAPI end point: %s", exception)
        raise CannotConnect from exception

    return True


class InvalidApiKey(HomeAssistantError):
    """Error to indicate there is an invalid api key."""


class CannotConnect(requests.exceptions.ConnectionError):
    """Error to indicate we cannot connect."""
