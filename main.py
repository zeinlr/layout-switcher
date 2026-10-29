"""
Layout Switcher - Portable background layout correction utility for Windows.
Main entry point.
"""

import ctypes
from ctypes import wintypes
import os
import sys

# Ensure local imports work when running directly or in PyInstaller bundle
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from tray_app import LayoutSwitcherTray
from win_api import ensure_interactive_desktop

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
user32.RegisterWindowMessageW.restype = wintypes.UINT

user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL

MUTEX_NAME = "Local\\LayoutSwitcher_SingleInstance_Mutex"
HWND_BROADCAST = 0xFFFF


def main():
    ensure_interactive_desktop()
    wm_show_settings = user32.RegisterWindowMessageW("LayoutSwitcher_ShowSettings_Message")

    mutex = kernel32.CreateMutexW(None, True, MUTEX_NAME)
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        # Application is already running in background!
        # Tell the running instance to open the Settings window.
        hwnd = user32.FindWindowW("LayoutSwitcher_Worker_Class", "LayoutSwitcher_Worker_Window")
        if hwnd:
            user32.PostMessageW(hwnd, wm_show_settings, 0, 0)
        else:
            user32.PostMessageW(HWND_BROADCAST, wm_show_settings, 0, 0)
        if mutex:
            kernel32.CloseHandle(mutex)
        sys.exit(0)

    try:
        show_settings = ("--settings" in sys.argv or "-s" in sys.argv)
        app = LayoutSwitcherTray(config_dir=BASE_DIR, show_settings_on_start=show_settings)
        app.start()
    finally:
        if mutex:
            kernel32.CloseHandle(mutex)


if __name__ == "__main__":
    main()
