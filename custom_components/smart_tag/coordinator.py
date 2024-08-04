"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SmartTagApiAuthError,
    SmartTagApiError,
)
from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SmartTagEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class SmartTagCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: SmartTagEntry

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),
        )

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            # return await self.config_entry.runtime_data.client.async_get_data()
            pass
        except SmartTagApiAuthError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except SmartTagApiError as exception:
            raise UpdateFailed(exception) from exception
