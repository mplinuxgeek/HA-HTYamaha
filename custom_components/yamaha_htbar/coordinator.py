"""DataUpdateCoordinator wrapping the BLE client."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import YamahaBarClient
from .const import DOMAIN, UPDATE_INTERVAL
from .protocol import BarState

_LOGGER = logging.getLogger(__name__)

type YamahaConfigEntry = ConfigEntry[YamahaCoordinator]


class YamahaCoordinator(DataUpdateCoordinator[BarState]):
    """Keeps the connection alive and surfaces pushed state to entities."""

    def __init__(
        self, hass: HomeAssistant, entry: YamahaConfigEntry, client: YamahaBarClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )
        self.client = client
        client.set_update_callback(self._on_push)

    @callback
    def _on_push(self) -> None:
        """Notification arrived; publish the latest state to entities."""
        self.async_set_updated_data(self.client.state)

    async def _async_update_data(self) -> BarState:
        """Connect if needed and poll a fresh snapshot (also a keep-alive)."""
        try:
            await self.client.ensure_connected()
            await self.client.refresh()
        except Exception as err:  # noqa: BLE001 - surface as unavailable
            raise UpdateFailed(str(err)) from err
        return self.client.state
