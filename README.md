# Yamaha Home Theater Sound Bar — Home Assistant (BLE)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Local-push Home Assistant integration that controls a Yamaha sound bar over
**Bluetooth LE** — no cloud, no network. Reverse-engineered from the official
*Home Theater Controller* app; the wire protocol is documented in
[`PROTOCOL.md`](PROTOCOL.md).

## Features

| Platform | Entities |
|----------|----------|
| `media_player` | Power, volume ± , mute, source, sound mode |
| `switch` | Clear Voice, Music Enhancer, Bass Extension, 3D Surround, UniVolume, Dialogue Lift, Adaptive DRC, Bluetooth Standby, HDMI Control |
| `select` | DSP Program |
| `button` | Treble / Bass / Subwoofer ± , menu navigation, memory presets |

It is a **control** integration: this BLE channel carries no media transport, so
there is no play/pause/now-playing. Volume and tone are relative (UP/DOWN) — the
media player exposes volume stepping, not an absolute slider.

## Installation

### HACS (recommended)

1. HACS → ⋮ → **Custom repositories**.
2. Add `https://github.com/bircoe/HA-HTYamaha` with category **Integration**.
3. Install **Yamaha Home Theater Sound Bar (BLE)**, then restart Home Assistant.

### Manual

Copy `custom_components/yamaha_htbar/` into your HA `config/custom_components/`
and restart.

## Setup

The bar is auto-discovered when in range (it advertises BLE service
`945ca2b0-…`) — accept the discovery in **Settings → Devices & Services**. To add
it manually, use **Add Integration → Yamaha Home Theater Sound Bar (BLE)** and
pick it from the discovered list.

Requires a working Bluetooth adapter / ESPHome Bluetooth proxy reachable by Home
Assistant.

## Requirements

- Home Assistant 2024.12.0 or newer.
- The sound bar within Bluetooth range of an HA-visible adapter or proxy.

## Notes & limitations

- **One BLE connection**, shared by all entities via a coordinator; state is
  pushed via GATT notifications with a 60 s keep-alive/reconnect poll.
- **`VOLUME_MAX`** in `const.py` (default 32) only scales the read-only volume
  bar; raise it if your model reports higher volume values.
- **Sound mode** and **DSP program** are optimistic (the protocol gives no clean
  readback for them); other state is read from the device.

## Disclaimer

Not affiliated with or endorsed by Yamaha. Provided as-is; the protocol was
derived by reverse engineering for interoperability.
