"""Media player entity (power / volume / mute / source / sound mode)."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import SOUND_MODE_SELECT, SOURCE_SELECT, VOLUME_MAX
from .coordinator import YamahaConfigEntry
from .entity import YamahaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YamahaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([YamahaMediaPlayer(entry.runtime_data)])


class YamahaMediaPlayer(YamahaEntity, MediaPlayerEntity):
    """The bar as a (control-only) media player.

    Volume is relative on this BLE channel, so only stepping is supported; the
    volume bar is read-only display scaled against VOLUME_MAX.
    """

    _attr_name = None  # main feature of the device
    _attr_source_list = list(SOURCE_SELECT)
    _attr_sound_mode_list = list(SOUND_MODE_SELECT)
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    )

    @property
    def unique_id(self) -> str:
        return self.client.address

    @property
    def state(self) -> MediaPlayerState | None:
        power = self.state_data.power
        if power is None:
            return None
        return MediaPlayerState.ON if power else MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        raw = self.state_data.volume_raw
        if raw is None:
            return None
        return max(0.0, min(1.0, raw / VOLUME_MAX))

    @property
    def is_volume_muted(self) -> bool | None:
        return self.state_data.muted

    @property
    def source(self) -> str | None:
        return self.state_data.source

    @property
    def sound_mode(self) -> str | None:
        return self.state_data.sound_mode

    async def async_turn_on(self) -> None:
        await self.client.set_power(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        await self.client.set_power(False)
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        await self.client.volume_up()
        await self.coordinator.async_request_refresh()

    async def async_volume_down(self) -> None:
        await self.client.volume_down()
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        await self.client.set_mute(mute)
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        await self.client.send_remote(SOURCE_SELECT[source])
        await self.coordinator.async_request_refresh()

    async def async_select_sound_mode(self, sound_mode: str) -> None:
        await self.client.send_remote(SOUND_MODE_SELECT[sound_mode])
        self.state_data.sound_mode = sound_mode  # optimistic, no readback
        self.async_write_ha_state()
