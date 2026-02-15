"""Tests for WeatherAPI integration."""

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.weatherapi.const import CONFIG_FORECAST, DOMAIN
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_form(hass: HomeAssistant) -> None:
    """Test config flow."""
    hass.config.latitude = 18.10
    hass.config.longitude = -77.29

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_invalid_api_key(hass: HomeAssistant) -> None:
    """Test that errors are shown when API key is invalid."""

    hass.config.latitude = 18.10
    hass.config.longitude = -77.29

    with patch(
        "custom_components.weatherapi.config_flow.is_valid_api_key",
        side_effect=AsyncMock(return_value=False),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: "invalid_api_key"}
        )

        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "invalid_api_key"}


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_create_entry(hass: HomeAssistant) -> None:
    """Test that entry is created."""

    hass.config.latitude = 18.10
    hass.config.longitude = -77.29

    with (
        patch(
            "custom_components.weatherapi.config_flow.is_valid_api_key",
            side_effect=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.weatherapi.coordinator.WeatherAPIUpdateCoordinator.get_weather",
            side_effect=AsyncMock(return_value={}),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: "api_key"}
        )

        assert result2["type"] == FlowResultType.CREATE_ENTRY


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_options_flow(hass: HomeAssistant) -> None:
    """Test config flow options."""
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


@pytest.mark.usefixtures("enable_custom_integrations")
async def test_options_flow_create_entry(hass: HomeAssistant) -> None:
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

        assert result2["type"] == FlowResultType.CREATE_ENTRY
