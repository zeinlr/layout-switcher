"""
Configuration manager for layout switcher.
"""

import json
import os
import sys
from win_api import (
    VK_F8,
    VK_PAUSE,
    VK_CAPITAL,
    MOD_SHIFT,
    MOD_CONTROL,
    MOD_ALT,
    MOD_WIN,
    MOD_NOREPEAT,
)

CONFIG_FILENAME = "config.json"

DEFAULT_CONFIG = {
    "hotkey": "F8",
    "show_tray_icon": False,
    "sound_notification": False,
}


def get_config_dir() -> str:
    """Returns directory where config.json should be stored."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

VK_MAP = {
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "PAUSE": VK_PAUSE, "BREAK": VK_PAUSE,
    "CAPSLOCK": VK_CAPITAL, "CAPITAL": VK_CAPITAL,
    "INSERT": 0x2D, "DELETE": 0x2E,
    "HOME": 0x24, "END": 0x23,
    "PAGEUP": 0x21, "PAGEDOWN": 0x22,
    "SPACE": 0x20, "TAB": 0x09,
}

# Add standard letters and digits
for i in range(ord('A'), ord('Z') + 1):
    VK_MAP[chr(i)] = i
for i in range(ord('0'), ord('9') + 1):
    VK_MAP[chr(i)] = i


def parse_hotkey_string(hotkey_str: str) -> tuple[int, int]:
    """
    Parse a hotkey string like 'F8', 'Pause', 'Shift+CapsLock', 'Ctrl+Shift+F8'
    Returns: (vk_code, modifiers)
    """
    parts = [p.strip().upper() for p in hotkey_str.split("+") if p.strip()]
    modifiers = MOD_NOREPEAT
    vk = VK_F8

    for p in parts:
        if p in ("CTRL", "CONTROL"):
            modifiers |= MOD_CONTROL
        elif p in ("SHIFT",):
            modifiers |= MOD_SHIFT
        elif p in ("ALT", "MENU"):
            modifiers |= MOD_ALT
        elif p in ("WIN", "WINDOWS"):
            modifiers |= MOD_WIN
        else:
            if p in VK_MAP:
                vk = VK_MAP[p]

    return vk, modifiers


def load_config(config_dir: str | None = None) -> dict:
    """Load config from disk or return default."""
    if not config_dir:
        config_dir = get_config_dir()
    cfg_path = os.path.join(config_dir, CONFIG_FILENAME)

    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass

    # Save default config if not present
    save_config(DEFAULT_CONFIG, config_dir)
    return DEFAULT_CONFIG.copy()


def save_config(config_data: dict, config_dir: str | None = None):
    """Save config dict to disk."""
    if not config_dir:
        config_dir = get_config_dir()
    cfg_path = os.path.join(config_dir, CONFIG_FILENAME)
    try:
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass
