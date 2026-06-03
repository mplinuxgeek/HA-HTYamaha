"""Select entity for the DSP program (no reliable readback -> optimistic)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DSP_SELECT
from .coordinator import YamahaConfigEntry
from .entity import YamahaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YamahaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([YamahaDspSelect(entry.runtime_data)])


class YamahaDspSelect(YamahaEntity, SelectEntity):
    """DSP / surround program selector."""

    _attr_translation_key = "dsp_program"
    _attr_options = list(DSP_SELECT)

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.client.address}_dsp_program"

    @property
    def current_option(self) -> str | None:
        return self.state_data.dsp_program

    async def async_select_option(self, option: str) -> None:
        await self.client.send_remote(DSP_SELECT[option])
        self.state_data.dsp_program = option  # optimistic
        self.async_write_ha_state()
