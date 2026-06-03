"""Button entities for stepped / momentary controls (relative protocol)."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import YamahaConfigEntry
from .entity import YamahaEntity


@dataclass(frozen=True, kw_only=True)
class YamahaButtonDescription(ButtonEntityDescription):
    """Maps a button to a remote action."""

    action: str


BUTTONS: tuple[YamahaButtonDescription, ...] = (
    # tone / subwoofer (relative; absolute value read back via reports)
    YamahaButtonDescription(key="treble_up", translation_key="treble_up", action="treble_up", entity_category=EntityCategory.CONFIG),
    YamahaButtonDescription(key="treble_down", translation_key="treble_down", action="treble_down", entity_category=EntityCategory.CONFIG),
    YamahaButtonDescription(key="bass_up", translation_key="bass_up", action="bass_up", entity_category=EntityCategory.CONFIG),
    YamahaButtonDescription(key="bass_down", translation_key="bass_down", action="bass_down", entity_category=EntityCategory.CONFIG),
    YamahaButtonDescription(key="swlevel_up", translation_key="swlevel_up", action="swlevel_up", entity_category=EntityCategory.CONFIG),
    YamahaButtonDescription(key="swlevel_down", translation_key="swlevel_down", action="swlevel_down", entity_category=EntityCategory.CONFIG),
    # menu navigation
    YamahaButtonDescription(key="menu_setup", translation_key="menu_setup", action="menu_setup"),
    YamahaButtonDescription(key="menu_info", translation_key="menu_info", action="menu_info"),
    YamahaButtonDescription(key="menu_option", translation_key="menu_option", action="menu_option"),
    YamahaButtonDescription(key="menu_up", translation_key="menu_up", action="menu_up"),
    YamahaButtonDescription(key="menu_down", translation_key="menu_down", action="menu_down"),
    YamahaButtonDescription(key="menu_left", translation_key="menu_left", action="menu_left"),
    YamahaButtonDescription(key="menu_right", translation_key="menu_right", action="menu_right"),
    YamahaButtonDescription(key="menu_enter", translation_key="menu_enter", action="menu_enter"),
    YamahaButtonDescription(key="menu_return", translation_key="menu_return", action="menu_return"),
    # memory presets
    YamahaButtonDescription(key="memory_ysp_l", translation_key="memory_ysp_l", action="memory_ysp_l"),
    YamahaButtonDescription(key="memory_ysp_c", translation_key="memory_ysp_c", action="memory_ysp_c"),
    YamahaButtonDescription(key="memory_ysp_r", translation_key="memory_ysp_r", action="memory_ysp_r"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YamahaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(YamahaButton(coordinator, desc) for desc in BUTTONS)


class YamahaButton(YamahaEntity, ButtonEntity):
    """Fires a single remote action."""

    entity_description: YamahaButtonDescription

    def __init__(self, coordinator, description: YamahaButtonDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.address}_{description.key}"

    async def async_press(self) -> None:
        await self.client.send_remote(self.entity_description.action)
        await self.coordinator.async_request_refresh()
