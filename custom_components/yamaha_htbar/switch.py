"""Switch entities for the bar's boolean sound features."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .client import YamahaBarClient
from .coordinator import YamahaConfigEntry
from .entity import YamahaEntity
from .protocol import BarState


@dataclass(frozen=True, kw_only=True)
class YamahaSwitchDescription(SwitchEntityDescription):
    """Describes a Yamaha switch."""

    is_on: Callable[[BarState], bool | None]
    set_fn: Callable[[YamahaBarClient, bool], Awaitable[None]]


def _remote_setter(on_action: str, off_action: str):
    async def _set(client: YamahaBarClient, on: bool) -> None:
        await client.send_remote(on_action if on else off_action)

    return _set


SWITCHES: tuple[YamahaSwitchDescription, ...] = (
    YamahaSwitchDescription(
        key="clearvoice",
        translation_key="clearvoice",
        is_on=lambda s: s.clearvoice,
        set_fn=_remote_setter("clearvoice_on", "clearvoice_off"),
    ),
    YamahaSwitchDescription(
        key="enhancer",
        translation_key="enhancer",
        is_on=lambda s: s.enhancer,
        set_fn=_remote_setter("enhancer_on", "enhancer_off"),
    ),
    YamahaSwitchDescription(
        key="bassext",
        translation_key="bassext",
        is_on=lambda s: s.bassext,
        set_fn=_remote_setter("bassext_on", "bassext_off"),
    ),
    YamahaSwitchDescription(
        key="surround3d",
        translation_key="surround3d",
        is_on=lambda s: s.surround3d,
        set_fn=_remote_setter("surround3d_on", "surround3d_off"),
    ),
    YamahaSwitchDescription(
        key="univolume",
        translation_key="univolume",
        is_on=lambda s: s.univolume,
        set_fn=_remote_setter("univolume_on", "univolume_off"),
    ),
    YamahaSwitchDescription(
        key="dialoglift",
        translation_key="dialoglift",
        is_on=lambda s: s.dialoglift,
        set_fn=_remote_setter("dialoglift_on", "dialoglift_off"),
    ),
    YamahaSwitchDescription(
        key="adaptive_drc",
        translation_key="adaptive_drc",
        is_on=lambda s: s.adaptive_drc,
        set_fn=lambda c, on: c.set_adaptive_drc(on),
    ),
    YamahaSwitchDescription(
        key="bt_standby",
        translation_key="bt_standby",
        is_on=lambda s: s.bt_standby,
        set_fn=lambda c, on: c.set_bt_standby(on),
    ),
    YamahaSwitchDescription(
        key="hdmi_control",
        translation_key="hdmi_control",
        is_on=lambda s: s.hdmi_control,
        set_fn=lambda c, on: c.set_hdmi_control(on),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YamahaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(YamahaSwitch(coordinator, desc) for desc in SWITCHES)


class YamahaSwitch(YamahaEntity, SwitchEntity):
    """A boolean sound feature."""

    entity_description: YamahaSwitchDescription

    def __init__(self, coordinator, description: YamahaSwitchDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.address}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.is_on(self.state_data)

    async def async_turn_on(self, **kwargs) -> None:
        await self.entity_description.set_fn(self.client, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.entity_description.set_fn(self.client, False)
        await self.coordinator.async_request_refresh()
