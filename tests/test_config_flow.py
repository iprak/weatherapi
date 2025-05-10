"""Tests for WeatherAPI integration."""

from unittest.mock import AsyncMock, patch
from http import HTTPStatus

from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.weatherapi.const import CONFIG_FORECAST, DOMAIN, TIMEZONE_URL
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant


async def test_form(hass: HomeAssistant, enable_custom_integrations) -> None:
    """Test we get the form."""
    hass.config.latitude = 18.10
    hass.config.longitude = -77.29

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}


async def test_invalid_api_key(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, enable_custom_integrations
) -> None:
    """Test that errors are shown when API key is invalid."""

    aioclient_mock.get(TIMEZONE_URL, status=HTTPStatus.BAD_REQUEST)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "invalid_api_key"}
    )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_api_key"}


async def test_create_entry(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, enable_custom_integrations
) -> None:
    """Test that entry is created."""

    aioclient_mock.get(TIMEZONE_URL, json={})  # Fake successful response

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "api_key"}
    )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY


async def test_options_flow(hass: HomeAssistant, enable_custom_integrations) -> None:
    """Test config flow options."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_create_entry(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    """Test that entry is creted from config flow options."""

    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    with patch("custom_components.weatherapi.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONFIG_FORECAST: False},
        )

        assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
