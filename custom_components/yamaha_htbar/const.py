"""Constants for the Yamaha Home Theater Sound Bar (BLE) integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "yamaha_htbar"

# --- BLE GATT ---------------------------------------------------------------
SERVICE_UUID: Final = "945ca2b0-852c-4ab8-b654-354df41c2795"
NOTIFY_UUID: Final = "5cafe9de-e7b0-4e0b-8fb9-2da91a7ae3ed"  # device -> app
WRITE_UUID: Final = "0c50e7fa-594c-408b-ae0d-b53b884b7c08"  # app -> device

# Spacing between consecutive writes. The app posts each command with a 100 ms
# delay; we stay a touch under that.
WRITE_GAP: Final = 0.08

# Keep-alive / state refresh interval (seconds). Doubles as a connection probe.
UPDATE_INTERVAL: Final = 60

# --- Frame opcodes (payload[0]) --------------------------------------------
OP_HELLO: Final = 0x01
OP_INFO_REQUEST: Final = 0x03
OP_REMOTE: Final = 0x40
OP_BT_STANDBY: Final = 0x42
OP_ADAPTIVE_DRC: Final = 0x45
OP_HDMI_CTRL: Final = 0x4E

HELLO_BODY: Final = b"HTS Cont"

# Report ids polled for state feedback (also pushed as notifications).
REPORT_POWER: Final = 0x10
REPORT_INPUT: Final = 0x11
REPORT_VOLUME: Final = 0x12  # mute + absolute volume
REPORT_SWLEVEL: Final = 0x13
REPORT_TONE: Final = 0x14
REPORT_SOUND: Final = 0x15  # output / dsp / feature flags

POLL_REPORTS: Final = (
    REPORT_POWER,
    REPORT_INPUT,
    REPORT_VOLUME,
    REPORT_SWLEVEL,
    REPORT_TONE,
    REPORT_SOUND,
)

# --- IR remote codes (opcode 0x40) ------------------------------------------
# NEC code -> the 0x40 command carries (address, command) i.e. bytes [0] and [2].
# Values are (addr, cmd). Source: Q.java in the decompiled APK.
REMOTE: Final[dict[str, tuple[int, int]]] = {
    # power
    "power_on": (0x78, 0x7E),
    "power_standby": (0x78, 0x7F),
    "power_toggle": (0x78, 0xCC),
    # mute
    "mute_on": (0x7E, 0xA2),
    "mute_off": (0x7E, 0xA3),
    "mute_toggle": (0x78, 0x9C),
    # volume / subwoofer (relative)
    "volume_up": (0x78, 0x1E),
    "volume_down": (0x78, 0x1F),
    "swlevel_up": (0x78, 0x4C),
    "swlevel_down": (0x78, 0x4D),
    # tone (relative)
    "treble_up": (0x78, 0x55),
    "treble_down": (0x78, 0x56),
    "bass_up": (0x78, 0x53),
    "bass_down": (0x78, 0x54),
    # sound feature toggles
    "clearvoice_on": (0x7E, 0x80),
    "clearvoice_off": (0x7E, 0x82),
    "enhancer_on": (0x7E, 0xD8),
    "enhancer_off": (0x7E, 0xD9),
    "bassext_on": (0x78, 0x6E),
    "bassext_off": (0x78, 0x6F),
    "surround3d_on": (0x78, 0xC9),
    "surround3d_off": (0x78, 0xB4),
    "univolume_on": (0x78, 0x7C),
    "univolume_off": (0x7E, 0x9C),
    "dialoglift_on": (0x7E, 0xB4),
    "dialoglift_off": (0x7E, 0xB7),
    # inputs
    "input_tv": (0x78, 0xDF),
    "input_hdmi1": (0x78, 0x4A),
    "input_hdmi2": (0x78, 0xD0),
    "input_hdmi3": (0x78, 0x2A),
    "input_hdmi4": (0x78, 0x41),
    "input_bluetooth": (0x78, 0x29),
    "input_analog": (0x78, 0xD1),
    "input_aux2": (0x78, 0xDE),
    "input_optical": (0x78, 0x49),
    # sound / beam modes
    "mode_surround": (0x78, 0xB4),
    "mode_stereo": (0x78, 0x50),
    "mode_3beam": (0x78, 0xC4),
    "mode_5beam": (0x78, 0xC2),
    "mode_st3beam": (0x78, 0xC3),
    "mode_target": (0x78, 0xC5),
    "mode_mysurround": (0x78, 0xC6),
    "mode_stereobeam": (0x7E, 0xC1),
    # DSP programs
    "dsp_off": (0x78, 0x9B),
    "dsp_movie": (0x78, 0xD9),
    "dsp_music": (0x78, 0xDA),
    "dsp_sports": (0x78, 0xDB),
    "dsp_game": (0x78, 0xDC),
    "dsp_drama": (0x7E, 0xFC),
    "dsp_scifi": (0x7E, 0xFA),
    "dsp_adventure": (0x7E, 0xFB),
    "dsp_spectacle": (0x7E, 0xF9),
    "dsp_concerthall": (0x7E, 0xE1),
    "dsp_jazzclub": (0x7E, 0xEC),
    "dsp_musicvideo": (0x7E, 0xF3),
    "dsp_talkshow": (0x7E, 0xF1),
    # menu navigation
    "menu_setup": (0x78, 0x9D),
    "menu_info": (0x78, 0x4E),
    "menu_option": (0x78, 0x2B),
    "menu_up": (0x78, 0x8E),
    "menu_down": (0x78, 0x8F),
    "menu_left": (0x78, 0x9F),
    "menu_right": (0x78, 0x9E),
    "menu_return": (0x78, 0xC0),
    "menu_enter": (0x78, 0xC1),
    # memory presets
    "memory_ysp_l": (0x78, 0x77),
    "memory_ysp_c": (0x78, 0x79),
    "memory_ysp_r": (0x78, 0x7B),
}

# --- Source mapping ---------------------------------------------------------
# Selectable sources (media_player.source_list) -> remote action name.
SOURCE_SELECT: Final[dict[str, str]] = {
    "TV": "input_tv",
    "HDMI 1": "input_hdmi1",
    "HDMI 2": "input_hdmi2",
    "HDMI 3": "input_hdmi3",
    "HDMI 4": "input_hdmi4",
    "Bluetooth": "input_bluetooth",
    "Analog": "input_analog",
    "AUX 2": "input_aux2",
    "Optical": "input_optical",
}

# Report 0x11 input index -> friendly name (full device table, read-only state).
SOURCE_INDEX_TO_NAME: Final[dict[int, str]] = {
    0: "HDMI 1",
    1: "HDMI 2",
    2: "HDMI 3",
    3: "HDMI 4",
    4: "BD/DVD",
    5: "Bluetooth",
    6: "USB",
    7: "TV",
    8: "AUX 1",
    9: "Portable",
    10: "Optical",
    11: "AUX 2",
    12: "Analog",
    13: "FM",
    14: "DAB",
    15: "Coaxial",
}

# --- Sound mode (media_player.sound_mode_list) ------------------------------
SOUND_MODE_SELECT: Final[dict[str, str]] = {
    "Surround": "mode_surround",
    "Stereo": "mode_stereo",
    "3 Beam": "mode_3beam",
    "5 Beam": "mode_5beam",
    "Stereo + 3 Beam": "mode_st3beam",
    "Target": "mode_target",
    "My Surround": "mode_mysurround",
    "Stereo Beam": "mode_stereobeam",
}

# --- DSP program (select entity) --------------------------------------------
DSP_SELECT: Final[dict[str, str]] = {
    "Off": "dsp_off",
    "Movie": "dsp_movie",
    "Music": "dsp_music",
    "Sports": "dsp_sports",
    "Game": "dsp_game",
    "Drama": "dsp_drama",
    "Sci-Fi": "dsp_scifi",
    "Adventure": "dsp_adventure",
    "Spectacle": "dsp_spectacle",
    "Concert Hall": "dsp_concerthall",
    "Jazz Club": "dsp_jazzclub",
    "Music Video": "dsp_musicvideo",
    "Talk Show": "dsp_talkshow",
}

# Approximate maximum raw volume value, used only to render the read-only
# volume_level bar. Volume control itself is relative (up/down). Adjust if your
# model reports higher values.
VOLUME_MAX: Final = 32
