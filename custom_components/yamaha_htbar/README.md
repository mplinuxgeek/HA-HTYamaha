# Yamaha Home Theater Sound Bar — BLE control integration

Local-push Home Assistant integration controlling a Yamaha sound bar over
Bluetooth LE. Reverse-engineered from the official app; protocol in
[`../../PROTOCOL.md`](../../PROTOCOL.md).

## Install

Copy `custom_components/yamaha_htbar/` into your HA `config/custom_components/`,
restart, then add via **Settings → Devices & Services**. The bar is
auto-discovered when in range (it advertises service `945ca2b0-…`); or add it
manually from the discovered list.

## Entities

| Platform | Entities |
|----------|----------|
| `media_player` | Power, volume ±, mute, source, sound mode |
| `switch` | Clear Voice, Music Enhancer, Bass Extension, 3D Surround, UniVolume, Dialogue Lift, Adaptive DRC, Bluetooth Standby, HDMI Control |
| `select` | DSP Program |
| `button` | Treble/Bass/Subwoofer ±, menu navigation, memory presets |

## Design notes

- **One BLE connection.** A `DataUpdateCoordinator` (`coordinator.py`) owns a
  single persistent GATT link (`client.py`); all entities share it. State is
  pushed via GATT notifications; a 60 s poll doubles as keep-alive / reconnect.
- **Control only.** This BLE channel carries no media transport/metadata, so the
  media player exposes power/volume/mute/source/sound-mode and no play/pause.
- **Relative volume & tone.** Volume, tone and subwoofer are UP/DOWN steps
  (hence `VOLUME_STEP` + buttons, not an absolute slider). Absolute values are
  read back from reports for display. Adjust `VOLUME_MAX` in `const.py` if your
  model's reported volume exceeds 32.
- **Optimistic state** for sound mode and DSP program (the protocol gives no
  clean readback for those).

## Tested

Protocol framing, checksums (all 68 IR codes), frame reassembly/resync and
report parsing are unit-verified. Live BLE behaviour depends on your model.
