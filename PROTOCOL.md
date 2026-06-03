# Yamaha Sound Bar — BLE Control Protocol

Reverse-engineered from `HOME THEATER CONTROLLER_3.08` APK (jadx decompile).
Core logic: `c.b.a.a.b.C` (protocol mgr), `c.b.a.a.a.aa` (BLE GATT), `c.b.a.a.b.Q/S`
(IR code table), `c.b.a.a.b.C0092s` (parsers/maps), `c.b.a.a.b.M` (key enum).

App supports two transports, chosen at runtime: **BLE GATT** (`C0054e`) and **SPP
RFCOMM** (`C0057h`, UUID `00001101-…`). HA should use BLE. SPP carries identical
framed payloads.

---

## 1. BLE transport

| Role | UUID |
|------|------|
| Service | `945ca2b0-852c-4ab8-b654-354df41c2795` |
| Notify (RX, device→app) | `5cafe9de-e7b0-4e0b-8fb9-2da91a7ae3ed` |
| Write (TX, app→device) | `0c50e7fa-594c-408b-ae0d-b53b884b7c08` |
| CCCD descriptor | `00002902-…` (standard) |

Connect flow (`aa.java`, `A.java`):
1. `connectGatt(transport=LE)`.
2. Scan filter = service UUID `945ca2b0…` (advertised). Match device by that.
3. On `onServicesDiscovered`: `requestConnectionPriority(HIGH)`.
4. Enable notifications on RX char `5cafe9de…` (write `01 00` to its CCCD).
5. Write frames to TX char `0c50e7fa…` (write-with-response, prop 0x08/0x04).
6. RX frames arrive as notifications on `5cafe9de…`.

No MTU negotiation in app. Default ATT MTU (23 → 20-byte payload). All control
commands fit in 20 bytes. Only `BEAM_SETUP` (0x47, 22-byte payload) exceeds it —
negotiate MTU ≥ 27 if you need beam setup; everything else is fine at default.

---

## 2. Frame format (both directions)

```
CC AA  LEN  PAYLOAD[LEN]  CHK
```
- `CC AA` = fixed header (`0xCC 0xAA`).
- `LEN` = length of PAYLOAD (1 byte).
- `PAYLOAD[0]` = opcode / report-id. Rest = opcode data.
- `CHK` = checksum: `(-(LEN + sum(PAYLOAD))) & 0xFF`.

**Validation rule** (TX & RX): `sum(bytes from LEN through CHK inclusive) & 0xFF == 0`.

Builder (`C.b(byte[])`):
```python
def frame(payload: bytes) -> bytes:
    ln = len(payload)            # must be <= 124
    body = bytes([ln]) + payload
    chk = (-(sum(body))) & 0xFF
    return b"\xCC\xAA" + body + bytes([chk])
```

RX parser (`C.a(byte[],int)`): re-syncs on `CC AA`, waits for `LEN+4` bytes,
verifies checksum, then dispatches `report_id = PAYLOAD[0]`, `data = PAYLOAD[1:]`.

---

## 3. Opcodes (TX, app→device)

`PAYLOAD[0]` = opcode:

| Opcode | Hex | Meaning | Payload after opcode |
|-------|-----|---------|----------------------|
| 1  | 0x01 | Handshake / hello | ASCII `"HTS Cont"` = `48 54 53 20 43 6F 6E 74` |
| 3  | 0x03 | Info request (poll a report) | `<report_id>` (see §5) |
| 64 | 0x40 | **Remote key** (IR code) | `<addr> <cmd>` — 2 bytes from IR table (§6) |
| 66 | 0x42 | Bluetooth standby on/off | `00`=off, `01`=on |
| 67 | 0x43 | Beam simple setup | 8 bytes: width/length/distance/offset (BE u16 ×4) |
| 68 | 0x44 | Test tone | `<type>` or `<type> <time> <signal>` |
| 69 | 0x45 | Adaptive DRC | `00`/`01` |
| 70 | 0x46 | IntelliBeam mode | `<mode>` (0/1/2) |
| 71 | 0x47 | Beam setup (full, 21 data bytes) | unit + 5×chlevel + 5×angle + 5×length + 5×focal |
| 72 | 0x48 | Beam channel level/angle | `<grpByte> <idxByte> <value>` |
| 73 | 0x49 | Image location | `<state> <Lch> <Rch>` |
| 74 | 0x4A | Target angle | `<angle>` |
| 75 | 0x4B | Volume trim (absolute) | `<trim>` |
| 76 | 0x4C | Display dimmer / OSD language | `<unit> <dimmer> <langByte>` |
| 77 | 0x4D | Beam output channel | `<chByte>` |
| 78 | 0x4E | HDMI control | `00`/`01` |
| 79 | 0x4F | HDMI-CEC command | `<value>` |

**Most control = opcode 0x40 (remote key).** Power, volume, mute, input, sound
modes, DSP, tone, etc. are all IR codes sent via 0x40 (§6).

> Volume & tone via 0x40 are **relative** (UP/DOWN steps). Absolute volume is not
> directly settable over BLE except `VOLUME_TRIM` (0x4B). To reach a target volume,
> read current volume from report 0x12 and send UP/DOWN repeatedly.

---

## 4. Recommended HA command set (opcode 0x40)

Pre-framed BLE bytes (write to `0c50e7fa…`):

| Action | Frame (hex) |
|--------|-------------|
| Power ON | `CC AA 03 40 78 7E C7` |
| Power STANDBY | `CC AA 03 40 78 7F C6` |
| Power TOGGLE | `CC AA 03 40 78 CC 79` |
| Mute ON | `CC AA 03 40 7E A2 9D` |
| Mute OFF | `CC AA 03 40 7E A3 9C` |
| Mute TOGGLE | `CC AA 03 40 78 9C A9` |
| Volume UP | `CC AA 03 40 78 1E 27` |
| Volume DOWN | `CC AA 03 40 78 1F 26` |
| Subwoofer level UP | `CC AA 03 40 78 4C F9` |
| Subwoofer level DOWN | `CC AA 03 40 78 4D F8` |
| Input TV | `CC AA 03 40 78 DF 66` |
| Input HDMI1 / BD/DVD | `CC AA 03 40 78 4A FB` |
| Input HDMI2 | `CC AA 03 40 78 D0 75` |
| Input HDMI3 | `CC AA 03 40 78 2A 1B` |
| Input HDMI4 | `CC AA 03 40 78 41 04` |
| Input Bluetooth | `CC AA 03 40 78 29 1C` |
| Input Analog/AUX1 | `CC AA 03 40 78 D1 74` |
| Input AUX2/Portable | `CC AA 03 40 78 DE 67` |
| Input Optical/Coaxial | `CC AA 03 40 78 49 FC` |
| Bass extension ON | `CC AA 03 40 78 6E D7` |
| Bass extension OFF | `CC AA 03 40 78 6F D6` |
| Clear Voice ON | `CC AA 03 40 7E 80 BF` |
| Clear Voice OFF | `CC AA 03 40 7E 82 BD` |
| 3D Surround ON | `CC AA 03 40 78 C9 7C` |
| 3D Surround OFF | `CC AA 03 40 78 B4 91` |
| Surround mode | `CC AA 03 40 78 B4 91` |
| Stereo mode | `CC AA 03 40 78 50 F5` |
| Treble UP / DOWN | `CC AA 03 40 78 55 F0` / `CC AA 03 40 78 56 EF` |
| Bass UP / DOWN | `CC AA 03 40 78 53 F2` / `CC AA 03 40 78 54 F1` |

Full IR list (90 codes: menus, DSP programs, beam modes, memory presets) in §6.

---

## 5. Reports (RX, device→app) — state feedback

Poll with `0x03 <id>`; device pushes same `id` as notification. `data = PAYLOAD[1:]`.
Parsers from `C0092s`:

| id | hex | Contents | Decode |
|----|-----|----------|--------|
| 16 | 0x10 | Power / BT-standby | `data[0]` bitmask: bit0=power, bit1=?, bit2=bt-standby, bit3, bit4 |
| 17 | 0x11 | Input | `data[0]` = input index (map §7) |
| 18 | 0x12 | Mute + Volume | `data[0]`!=0 → muted; `data[1]` = volume (raw, absolute) |
| 19 | 0x13 | Subwoofer level | `data[0]` scaled by model table |
| 20 | 0x14 | Tone | `data[0]`=treble, `data[1]`=bass |
| 21 | 0x15 | Sound flags | `data[0]`=output, `data[1..2]`=dsp, `data[3]` bitmask: b0=enhancer b1=univolume b2=clearvoice b3=dialoglift b4=adaptivedrc b5=bassext b6=3dsurround |
| 22 | 0x16 | (system info) | — |
| 23 | 0x17 | Setup id/dims | id + width/length/distance/offset (BE u16) |
| 24 | 0x18 | Input assign | `data[0..7]` = TV,AUX1,AUX2,HDMI1-4,ARC |
| 25 | 0x19 | IntelliBeam state | `data[0]` via map |
| 26 | 0x1A | Beam params | unit + ch levels + angles + lengths + focals |
| 27 | 0x1B | Image location | — |
| 28 | 0x1C | Target angle | — |
| 29 | 0x1D | Volume trim | — |
| 30 | 0x1E | Dimmer / OSD lang | — |
| 31 | 0x1F | Display state | — |
| 32 | 0x20 | Bluetooth codec | — |
| 33 | 0x21 | Beam output ch | — |
| 35 | 0x23 | HDMI-CEC state/addr | `data` → CEC state, CEC address |

Report 0x10 power decode (`C0092s.l`): `power = data[0] & 0x01`,
`bt_standby = (data[0] >> 2) & 0x01`.
Report 0x12 (`C0092s.r`): `muted = data[0] != 0`, `volume = data[1]` (signed byte).

ACK/NACK: report `0x00` carries `data[0]`=echoed cmd, `data[1]`=status (0 = ack).

**Suggested HA poll set on connect:** request 0x10, 0x11, 0x12, 0x15 for
power/input/volume/mute/sound state, then rely on push notifications.

---

## 6. Full IR remote code table (opcode 0x40)

Source `Q.java`. IR is NEC-style 4 bytes `[addr, ~addr, cmd, ~cmd]`. The 0x40
command transmits `[addr, cmd]` (bytes 0 and 2). Frame = `CC AA 03 40 <addr> <cmd> <chk>`.

```
NAME                         addr cmd   frame
REM_POWER                    78   CC    CC AA 03 40 78 CC 79
REM_POWER_ON                 78   7E    CC AA 03 40 78 7E C7
REM_POWER_STANDBY            78   7F    CC AA 03 40 78 7F C6
REM_MUTE                     78   9C    CC AA 03 40 78 9C A9
REM_MUTE_ON                  7E   A2    CC AA 03 40 7E A2 9D
REM_MUTE_OFF                 7E   A3    CC AA 03 40 7E A3 9C
REM_VOLUME_UP                78   1E    CC AA 03 40 78 1E 27
REM_VOLUME_DOWN              78   1F    CC AA 03 40 78 1F 26
REM_SWLEVEL_UP               78   4C    CC AA 03 40 78 4C F9
REM_SWLEVEL_DOWN             78   4D    CC AA 03 40 78 4D F8
REM_CLEARVOICE               78   5C    CC AA 03 40 78 5C E9
REM_CLEARVOICE_ON            7E   80    CC AA 03 40 7E 80 BF
REM_CLEARVOICE_OFF           7E   82    CC AA 03 40 7E 82 BD
REM_UNIVOLUME                78   8A    CC AA 03 40 78 8A BB
REM_UNIVOLUME_ON             78   7C    CC AA 03 40 78 7C C9
REM_UNIVOLUME_OFF            7E   9C    CC AA 03 40 7E 9C A3
REM_ENHANCER                 78   CB    CC AA 03 40 78 CB 7A
REM_ENHANCER_ON              7E   D8    CC AA 03 40 7E D8 67
REM_ENHANCER_OFF             7E   D9    CC AA 03 40 7E D9 66
REM_DIALOGLIFG               78   33    CC AA 03 40 78 33 12
REM_DIALOGLIFG_ON            7E   B4    CC AA 03 40 7E B4 8B
REM_DIALOGLIFG_OFF           7E   B7    CC AA 03 40 7E B7 88
REM_BASSEXT                  78   8B    CC AA 03 40 78 8B BA
REM_BASSEXT_ON               78   6E    CC AA 03 40 78 6E D7
REM_BASSEXT_OFF              78   6F    CC AA 03 40 78 6F D6
REM_3DSURROUND_ON            78   C9    CC AA 03 40 78 C9 7C
REM_3DSURROUND_OFF           78   B4    CC AA 03 40 78 B4 91
REM_MEMORY_LOAD_YSPL         78   77    CC AA 03 40 78 77 CE
REM_MEMORY_LOAD_YSPC         78   79    CC AA 03 40 78 79 CC
REM_MEMORY_LOAD_YSPR         78   7B    CC AA 03 40 78 7B CA
REM_INPUT_TV                 78   DF    CC AA 03 40 78 DF 66
REM_INPUT_BULETOOTH          78   29    CC AA 03 40 78 29 1C
REM_INPUT_AUX1               78   D1    CC AA 03 40 78 D1 74
REM_INPUT_ANALOG             78   D1    CC AA 03 40 78 D1 74
REM_INPUT_AUX2               78   DE    CC AA 03 40 78 DE 67
REM_INPUT_PORTABLE           78   DE    CC AA 03 40 78 DE 67
REM_INPUT_OPTICAL            78   49    CC AA 03 40 78 49 FC
REM_INPUT_COAXIAL            78   49    CC AA 03 40 78 49 FC
REM_INPUT_HDMI1              78   4A    CC AA 03 40 78 4A FB
REM_INPUT_BDDVD              78   4A    CC AA 03 40 78 4A FB
REM_INPUT_HDMI2              78   D0    CC AA 03 40 78 D0 75
REM_INPUT_HDMI3              78   2A    CC AA 03 40 78 2A 1B
REM_INPUT_HDMI4              78   41    CC AA 03 40 78 41 04
REM_TONE_TREBLE_UP           78   55    CC AA 03 40 78 55 F0
REM_TONE_TREBLE_DOWN         78   56    CC AA 03 40 78 56 EF
REM_TONE_BASS_UP             78   53    CC AA 03 40 78 53 F2
REM_TONE_BASS_DOWN           78   54    CC AA 03 40 78 54 F1
REM_MENU_SETUP               78   9D    CC AA 03 40 78 9D A8
REM_MENU_INFO                78   4E    CC AA 03 40 78 4E F7
REM_MENU_OPTION              78   2B    CC AA 03 40 78 2B 1A
REM_MENU_UP                  78   8E    CC AA 03 40 78 8E B7
REM_MENU_DOWN                78   8F    CC AA 03 40 78 8F B6
REM_MENU_RIGHT               78   9E    CC AA 03 40 78 9E A7
REM_MENU_LEFT                78   9F    CC AA 03 40 78 9F A6
REM_MENU_RETURN              78   C0    CC AA 03 40 78 C0 85
REM_MENU_ENTER               78   C1    CC AA 03 40 78 C1 84
REM_MODE_5BEAM               78   C2    CC AA 03 40 78 C2 83
REM_MODE_ST3BEAM             78   C3    CC AA 03 40 78 C3 82
REM_MODE_3BEAM               78   C4    CC AA 03 40 78 C4 81
REM_MODE_SURROUND            78   B4    CC AA 03 40 78 B4 91
REM_MODE_TARGET              78   C5    CC AA 03 40 78 C5 80
REM_MODE_MYSURROUND          78   C6    CC AA 03 40 78 C6 7F
REM_MODE_STEREO_BEAM         7E   C1    CC AA 03 40 7E C1 7E
REM_MODE_STEREO              78   50    CC AA 03 40 78 50 F5
REM_MODE_STEREO_DIRECT       78   50    CC AA 03 40 78 50 F5
REM_DSP_OFF                  78   9B    CC AA 03 40 78 9B AA
REM_DSP_OFF_TVPROGRAM        78   9B    CC AA 03 40 78 9B AA
REM_DSP_TALKSHOW             7E   F1    CC AA 03 40 7E F1 4E
REM_DSP_TVPROGRAM            7E   F1    CC AA 03 40 7E F1 4E
REM_DSP_GROUP_MOVIE          78   D9    CC AA 03 40 78 D9 6C
REM_DSP_MOVIE                78   D9    CC AA 03 40 78 D9 6C
REM_DSP_GROUP_MUSIC          78   DA    CC AA 03 40 78 DA 6B
REM_DSP_MUSIC                78   DA    CC AA 03 40 78 DA 6B
REM_DSP_GROUP_ENTERTAINMENT  78   DB    CC AA 03 40 78 DB 6A
REM_DSP_SPECTACLE            7E   F9    CC AA 03 40 7E F9 46
REM_DSP_SCIFI                7E   FA    CC AA 03 40 7E FA 45
REM_DSP_ADVENTURE            7E   FB    CC AA 03 40 7E FB 44
REM_DSP_CONCERTHALL          7E   E1    CC AA 03 40 7E E1 5E
REM_DSP_JAZZCLUB             7E   EC    CC AA 03 40 7E EC 53
REM_DSP_MUSICVIDEO           7E   F3    CC AA 03 40 7E F3 4C
REM_DSP_DRAMA                7E   FC    CC AA 03 40 7E FC 43
REM_DSP_GAME                 78   DC    CC AA 03 40 78 DC 69
REM_DSP_SPORTS               78   DB    CC AA 03 40 78 DB 6A
REM_DSP_DTS3D                78   C9    CC AA 03 40 78 C9 7C
REM_DSP_SPORTS_2500          7E   F8    CC AA 03 40 7E F8 47
REM_DSP_GAME_2500            7E   CE    CC AA 03 40 7E CE 71
REM_MODE_STEREO_DIRECT_2500  7E   C0    CC AA 03 40 7E C0 7F
```

The `_2500` variants and DSP fallbacks are selected by model (`P.a(String)` swaps
in model-specific codes for some YSP/ATS models). Most bars use the primary code.

---

## 7. Lookup maps (value index → action)

Input index (report 0x11 / `C0092s.e`):
```
0 HDMI1   1 HDMI2   2 HDMI3   3 HDMI4   4 BD/DVD   5 Bluetooth
6 USB     7 TV      8 AUX1    9 Portable 10 Optical 11 AUX2
12 Analog 13 FM    14 DAB    15 Coaxial
```

Sound mode index (`C0092s.f`):
```
0 Surround  1 StereoDirect  2 Target  3 5Beam  4 St3Beam  5 3Beam
6 MySurround 7 5Beam  8 St3Beam  9 StereoBeam  10 Stereo  255 (none)
```

DSP program index (`C0092s.g`):
```
0 Off  1 Off(TVProg)  2 TVProgram  3 SciFi  4 Spectacle  5 Adventure
6 MusicVideo 7 ConcertHall 8 JazzClub 9 Sports 10 TalkShow 11 Drama
12 Game 13 StereoDirect 14 StereoBeam 15 Movie 16 Music 17 GroupMovie
18 GroupMusic 19 Stereo 20 Target 21 DTS3D
```

IntelliBeam mode (`C0092s.d`): 0,1,2 → bytes 0,1,2.
OSD language (`C0092s.k`): 0→0x11, 1→0x21, 2→0x41, 3→0x81.
Test-tone type (`C0092s.f718b/f719c`).

---

## 8. Android permissions (manifest)

`BLUETOOTH`, `BLUETOOTH_ADMIN`, `ACCESS_FINE_LOCATION` (BLE scan),
`ACCESS_NETWORK_STATE`, `INTERNET`. On Linux/BlueZ for HA these map to standard
BLE GATT client ops — no special perms.

---

## 9. HA integration notes

- Use **bleak** (HA's `bluetooth` stack / `BleakClient`).
- Subscribe to notify char `5cafe9de…`; write to `0c50e7fa…`.
- On connect: send handshake `CC AA 09 01 48 54 53 20 43 6F 6E 74 <chk>`, then poll
  reports 0x10/0x11/0x12/0x15.
- `media_player` mapping:
  - power → 0x40 POWER_ON / POWER_STANDBY; state from report 0x10 bit0.
  - volume → relative UP/DOWN (0x40); state (absolute) from report 0x12 `data[1]`.
    Volume range is model-specific — derive min/max from observed report values.
  - mute → 0x40 MUTE_ON/OFF; state from report 0x12 `data[0]`.
  - source → input IR codes; state from report 0x11 index (map §7).
  - sound_mode → DSP/mode IR codes; state from report 0x15.
- Frames are tiny; throttle writes (~100 ms, app uses 100 ms post-delay per cmd).
