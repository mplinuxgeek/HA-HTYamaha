"""Frame (de)serialisation and state parsing for the Yamaha sound bar."""

from __future__ import annotations

from dataclasses import dataclass, field

from .const import (
    OP_HELLO,
    OP_INFO_REQUEST,
    OP_REMOTE,
    HELLO_BODY,
    REPORT_INPUT,
    REPORT_POWER,
    REPORT_SOUND,
    REPORT_SWLEVEL,
    REPORT_TONE,
    REPORT_VOLUME,
    SOURCE_INDEX_TO_NAME,
)

HEADER = bytes((0xCC, 0xAA))


def build_frame(payload: bytes) -> bytes:
    """Wrap *payload* in the CC AA <len> <payload> <chk> frame."""
    if not 0 < len(payload) <= 124:
        raise ValueError("payload length out of range")
    body = bytes((len(payload),)) + payload
    chk = (-sum(body)) & 0xFF
    return HEADER + body + bytes((chk,))


def remote_frame(addr: int, cmd: int) -> bytes:
    """Frame for an IR remote code (opcode 0x40)."""
    return build_frame(bytes((OP_REMOTE, addr & 0xFF, cmd & 0xFF)))


def hello_frame() -> bytes:
    """Initial handshake frame."""
    return build_frame(bytes((OP_HELLO,)) + HELLO_BODY)


def info_request_frame(report_id: int) -> bytes:
    """Frame requesting the device to report *report_id*."""
    return build_frame(bytes((OP_INFO_REQUEST, report_id & 0xFF)))


def _s8(value: int) -> int:
    """Interpret a byte as a signed 8-bit integer."""
    return value - 256 if value >= 128 else value


class FrameDecoder:
    """Reassembles a byte stream into complete (report_id, data) frames.

    Mirrors the resync logic in the app: scan for the ``CC AA`` header, wait for
    ``len + 4`` bytes, verify the checksum, then emit the payload.
    """

    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, data: bytes) -> list[tuple[int, bytes]]:
        """Add received bytes; return any complete frames decoded."""
        self._buf.extend(data)
        out: list[tuple[int, bytes]] = []
        while True:
            # Drop bytes until a header start is plausible.
            start = self._buf.find(0xCC)
            if start == -1:
                self._buf.clear()
                break
            if start:
                del self._buf[:start]
            if len(self._buf) < 2:
                break
            if self._buf[1] != 0xAA:
                # False positive header byte; drop it and keep scanning.
                del self._buf[0]
                continue
            if len(self._buf) < 3:
                break
            length = self._buf[2]
            total = length + 4  # CC AA len ... chk
            if len(self._buf) < total:
                break
            frame = bytes(self._buf[:total])
            del self._buf[:total]
            # Checksum: sum of bytes from len byte through chk == 0 mod 256.
            if (sum(frame[2:total]) & 0xFF) == 0:
                payload = frame[3 : 3 + length]
                if payload:
                    out.append((payload[0], payload[1:]))
        return out


@dataclass
class BarState:
    """Decoded sound bar state. ``None`` means unknown."""

    power: bool | None = None
    bt_standby: bool | None = None
    source: str | None = None
    source_index: int | None = None
    muted: bool | None = None
    volume_raw: int | None = None
    treble: int | None = None
    bass: int | None = None
    swlevel: int | None = None
    enhancer: bool | None = None
    univolume: bool | None = None
    clearvoice: bool | None = None
    dialoglift: bool | None = None
    adaptive_drc: bool | None = None
    bassext: bool | None = None
    surround3d: bool | None = None
    # Optimistic-only (no reliable readback): set when we send the command.
    sound_mode: str | None = None
    dsp_program: str | None = None
    hdmi_control: bool | None = None
    raw: dict[int, bytes] = field(default_factory=dict)

    def apply(self, report_id: int, data: bytes) -> None:
        """Update fields from a decoded report. Unknown reports are ignored."""
        self.raw[report_id] = data
        if report_id == REPORT_POWER and data:
            self.power = bool(data[0] & 0x01)
            self.bt_standby = bool(data[0] & 0x04)
        elif report_id == REPORT_INPUT and data:
            self.source_index = data[0]
            self.source = SOURCE_INDEX_TO_NAME.get(data[0], f"Input {data[0]}")
        elif report_id == REPORT_VOLUME and len(data) >= 2:
            self.muted = data[0] != 0
            self.volume_raw = data[1] & 0xFF
        elif report_id == REPORT_SWLEVEL and data:
            self.swlevel = _s8(data[0])
        elif report_id == REPORT_TONE and len(data) >= 2:
            self.treble = _s8(data[0])
            self.bass = _s8(data[1])
        elif report_id == REPORT_SOUND and len(data) >= 4:
            flags = data[3]
            self.enhancer = bool(flags & 0x01)
            self.univolume = bool(flags & 0x02)
            self.clearvoice = bool(flags & 0x04)
            self.dialoglift = bool(flags & 0x08)
            self.adaptive_drc = bool(flags & 0x10)
            self.bassext = bool(flags & 0x20)
            self.surround3d = bool(flags & 0x40)
