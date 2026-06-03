"""BLE connection + command client for the Yamaha sound bar."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from bleak.backends.device import BLEDevice
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    establish_connection,
)

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant

from .const import (
    NOTIFY_UUID,
    OP_ADAPTIVE_DRC,
    OP_BT_STANDBY,
    OP_HDMI_CTRL,
    POLL_REPORTS,
    REMOTE,
    WRITE_GAP,
    WRITE_UUID,
)
from .protocol import (
    BarState,
    FrameDecoder,
    build_frame,
    hello_frame,
    info_request_frame,
    remote_frame,
)

_LOGGER = logging.getLogger(__name__)


class YamahaBarClient:
    """Maintains a GATT connection and exposes high-level commands."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        self._hass = hass
        self._address = address
        self._name = name
        self._client: BleakClientWithServiceCache | None = None
        self._decoder = FrameDecoder()
        self._write_lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()
        self.state = BarState()
        self._update_cb: Callable[[], None] | None = None

    @property
    def address(self) -> str:
        return self._address

    def set_update_callback(self, cb: Callable[[], None]) -> None:
        """Register a callback fired whenever state changes from a notification."""
        self._update_cb = cb

    @property
    def connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    async def ensure_connected(self) -> None:
        """Connect if not already connected. Raises on failure."""
        if self.connected:
            return
        async with self._connect_lock:
            if self.connected:
                return
            ble_device = bluetooth.async_ble_device_from_address(
                self._hass, self._address, connectable=True
            )
            if ble_device is None:
                raise ConnectionError(
                    f"{self._name} ({self._address}) not in range"
                )
            self._client = await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                self._name,
                disconnected_callback=self._on_disconnect,
            )
            await self._client.start_notify(NOTIFY_UUID, self._on_notify)
            await self._send(hello_frame())
            await self.refresh()
            _LOGGER.debug("Connected to %s", self._name)

    async def disconnect(self) -> None:
        client, self._client = self._client, None
        if client is not None:
            try:
                await client.disconnect()
            except Exception:  # noqa: BLE001 - best effort on teardown
                pass

    def _on_disconnect(self, _client: BleakClientWithServiceCache) -> None:
        _LOGGER.debug("%s disconnected", self._name)
        self._client = None
        self._decoder = FrameDecoder()

    def _on_notify(
        self, _char: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        changed = False
        for report_id, payload in self._decoder.feed(bytes(data)):
            self.state.apply(report_id, payload)
            changed = True
        if changed and self._update_cb is not None:
            self._update_cb()

    async def _send(self, frame: bytes) -> None:
        if not self.connected:
            await self.ensure_connected()
        assert self._client is not None
        async with self._write_lock:
            await self._client.write_gatt_char(WRITE_UUID, frame, response=True)
            await asyncio.sleep(WRITE_GAP)

    async def refresh(self) -> None:
        """Poll all state reports."""
        for report_id in POLL_REPORTS:
            await self._send(info_request_frame(report_id))

    # --- high level commands ------------------------------------------------
    async def send_remote(self, action: str) -> None:
        """Send a named IR remote action (see const.REMOTE)."""
        addr, cmd = REMOTE[action]
        await self._send(remote_frame(addr, cmd))

    async def set_power(self, on: bool) -> None:
        await self.send_remote("power_on" if on else "power_standby")

    async def set_mute(self, mute: bool) -> None:
        await self.send_remote("mute_on" if mute else "mute_off")

    async def volume_up(self) -> None:
        await self.send_remote("volume_up")

    async def volume_down(self) -> None:
        await self.send_remote("volume_down")

    async def set_bt_standby(self, on: bool) -> None:
        await self._send(build_frame(bytes((OP_BT_STANDBY, 1 if on else 0))))

    async def set_adaptive_drc(self, on: bool) -> None:
        await self._send(build_frame(bytes((OP_ADAPTIVE_DRC, 1 if on else 0))))

    async def set_hdmi_control(self, on: bool) -> None:
        await self._send(build_frame(bytes((OP_HDMI_CTRL, 1 if on else 0))))
