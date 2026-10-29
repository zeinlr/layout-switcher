r"""
Windows Autostart manager via HKCU\Software\Microsoft\Windows\CurrentVersion\Run.
Requires no administrator privileges, fully portable.
"""

import os
import sys
import winreg

APP_NAME = "LayoutSwitcher"
REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def get_executable_command() -> str:
    """Returns properly quoted path to the current executable or script."""
    exe = os.path.abspath(sys.argv[0])
    if not exe.lower().endswith(".exe"):
        return f'"{sys.executable}" "{exe}"'
    return f'"{exe}"'


def is_autostart_enabled() -> bool:
    """Check if the application is registered in Windows autostart."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, APP_NAME)
            return bool(val)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def set_autostart(enable: bool) -> bool:
    """Enable or disable autostart in Windows registry."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                cmd = get_executable_command()
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False


def toggle_autostart() -> bool:
    """Toggle autostart status and return new state."""
    current = is_autostart_enabled()
    target = not current
    set_autostart(target)
    return is_autostart_enabled()
