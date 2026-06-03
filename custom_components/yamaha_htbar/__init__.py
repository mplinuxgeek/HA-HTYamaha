"""The Yamaha Home Theater Sound Bar (BLE) integration."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .client import YamahaBarClient
from .coordinator import YamahaConfigEntry, YamahaCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: YamahaConfigEntry) -> bool:
    """Set up Yamaha sound bar from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    client = YamahaBarClient(hass, address, entry.title)
    coordinator = YamahaCoordinator(hass, entry, client)

    await coordinator.async_config_entry_first_refresh()
    if not client.connected:
        raise ConfigEntryNotReady(f"Could not connect to {entry.title}")

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: YamahaConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.client.disconnect()
    return unload_ok
