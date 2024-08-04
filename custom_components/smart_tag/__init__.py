"""
Custom integration to integrate smart_tag with Home Assistant.

For more details about this integration, please refer to
to https://github.com/grimsteel/homeassistant-smart-tag
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from custom_components.smart_tag.const import CONF_API_CLIENT

from .api import SmartTagApiClient
from .coordinator import SmartTagCoordinator
from .data import SmartTagData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SmartTagEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: SmartTagEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = SmartTagCoordinator(
        hass=hass,
    )
    entry.runtime_data = SmartTagData(
        client=entry.data[CONF_API_CLIENT]
        or SmartTagApiClient(
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: SmartTagEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: SmartTagEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
