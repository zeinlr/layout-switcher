"""
System Tray & Background Worker Application using Win32 API.
Zero dependencies, minimal memory footprint (< 15 MB RAM), 0% idle CPU.
Supports stealth background mode (no tray icon), hotkey correction,
and on-demand Settings UI on repeat launch or shortcut.
"""

import ctypes
from ctypes import wintypes
import os
import threading
import time

from autostart import is_autostart_enabled, toggle_autostart
from config import load_config, parse_hotkey_string, get_config_dir
from core import perform_correction
from win_api import (
    user32,
    kernel32,
    shell32,
    ensure_interactive_desktop,
    WNDCLASSW,
    WNDPROCTYPE,
    NOTIFYICONDATAW,
    LRESULT,
    WM_HOTKEY,
    WM_USER,
    WM_TRAYICON,
    WM_RBUTTONUP,
    WM_LBUTTONUP,
    WM_CONTEXTMENU,
    WM_CLOSE,
    WM_DESTROY,
    WM_QUIT,
    MOD_CONTROL,
    MOD_SHIFT,
    MOD_NOREPEAT,
    VK_F8,
)

# Constants
NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010

IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010

MF_STRING = 0x00000000
MF_CHECKED = 0x00000008
MF_UNCHECKED = 0x00000000
MF_SEPARATOR = 0x00000800
MF_GRAYED = 0x00000001

TPM_RIGHTBUTTON = 0x0002
TPM_RETURNCMD = 0x0100

ID_HOTKEY_MAIN = 1001
ID_HOTKEY_SETTINGS = 1002

ID_MENU_SETTINGS = 2000
ID_MENU_STATUS = 2001
ID_MENU_HOTKEY_INFO = 2002
ID_MENU_AUTOSTART = 2003
ID_MENU_TRIGGER_NOW = 2004
ID_MENU_EXIT = 2005

WINDOW_CLASS = "LayoutSwitcher_Worker_Class"
WINDOW_TITLE = "LayoutSwitcher_Worker_Window"

user32.ChangeWindowMessageFilter.argtypes = [wintypes.UINT, wintypes.DWORD]
user32.ChangeWindowMessageFilter.restype = wintypes.BOOL

user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
user32.RegisterWindowMessageW.restype = wintypes.UINT

user32.LoadImageW.argtypes = [
    wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
    ctypes.c_int, ctypes.c_int, wintypes.UINT
]
user32.LoadImageW.restype = wintypes.HANDLE

user32.LoadIconW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR]
user32.LoadIconW.restype = wintypes.HICON

user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL

user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.TranslateMessage.restype = wintypes.BOOL

user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
user32.DispatchMessageW.restype = LRESULT


class LayoutSwitcherTray:
    def __init__(self, config_dir: str | None = None, show_settings_on_start: bool = False):
        self.config_dir = config_dir or get_config_dir()
        self.config = load_config(self.config_dir)
        self.hotkey_str = self.config.get("hotkey", "F8")
        self.vk, self.modifiers = parse_hotkey_string(self.hotkey_str)
        self.show_settings_on_start = show_settings_on_start

        self.hwnd = None
        self.thread_id = None
        self.hinstance = kernel32.GetModuleHandleW(None)
        self.class_name = WINDOW_CLASS
        self.window_title = WINDOW_TITLE
        self.is_paused = False
        self.nid = NOTIFYICONDATAW()
        self.tray_icon_added = False
        self.is_running = False
        self._proc_delegate = None

        # Custom window messages for inter-process communication
        self.wm_show_settings = user32.RegisterWindowMessageW("LayoutSwitcher_ShowSettings_Message")
        self.wm_exit_app = user32.RegisterWindowMessageW("LayoutSwitcher_Exit_Message")

    def _get_icon_handle(self) -> wintypes.HICON:
        icon_path = os.path.join(self.config_dir, "icon.ico")
        if os.path.exists(icon_path):
            hicon = user32.LoadImageW(None, icon_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
            if hicon:
                return hicon
        return user32.LoadIconW(None, ctypes.cast(32512, wintypes.LPCWSTR))

    def _update_tray_icon(self):
        if not self.hwnd or not self.tray_icon_added:
            return
        status_text = "Приостановлен" if self.is_paused else "Активен"
        tip = f"Layout Switcher ({self.hotkey_str}) - {status_text}"
        self.nid.szTip = tip[:127]
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self.nid))

    def _show_tray_icon(self):
        if not self.hwnd:
            return
        if not self.tray_icon_added:
            self.nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            self.nid.hWnd = self.hwnd
            self.nid.uID = 1
            self.nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
            self.nid.uCallbackMessage = WM_TRAYICON
            self.nid.hIcon = self._get_icon_handle()
            tip = f"Layout Switcher ({self.hotkey_str}) - Активен"
            self.nid.szTip = tip[:127]
            shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(self.nid))
            self.tray_icon_added = True
        else:
            self._update_tray_icon()

    def _hide_tray_icon(self):
        if self.hwnd and self.tray_icon_added:
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self.nid))
            self.tray_icon_added = False

    def _show_context_menu(self):
        hmenu = user32.CreatePopupMenu()
        if not hmenu:
            return

        status_flag = MF_UNCHECKED if self.is_paused else MF_CHECKED
        status_label = "Приостановить (Пауза)" if not self.is_paused else "Включить (Активен)"
        autostart_flag = MF_CHECKED if is_autostart_enabled() else MF_UNCHECKED

        user32.AppendMenuW(hmenu, MF_STRING, ID_MENU_SETTINGS, "Настройки...")
        user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(hmenu, MF_STRING | status_flag, ID_MENU_STATUS, status_label)
        user32.AppendMenuW(hmenu, MF_STRING | MF_GRAYED, ID_MENU_HOTKEY_INFO, f"Горячая клавиша: {self.hotkey_str}")
        user32.AppendMenuW(hmenu, MF_STRING | autostart_flag, ID_MENU_AUTOSTART, "Автозапуск с Windows")
        user32.AppendMenuW(hmenu, MF_STRING, ID_MENU_TRIGGER_NOW, f"Исправить сейчас ({self.hotkey_str})")
        user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(hmenu, MF_STRING, ID_MENU_EXIT, "Выход")

        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))

        user32.SetForegroundWindow(self.hwnd)
        cmd = user32.TrackPopupMenuEx(
            hmenu,
            TPM_RIGHTBUTTON | TPM_RETURNCMD,
            pt.x, pt.y,
            self.hwnd,
            None
        )
        user32.DestroyMenu(hmenu)

        if cmd == ID_MENU_SETTINGS:
            self.open_settings_async()
        elif cmd == ID_MENU_STATUS:
            self.is_paused = not self.is_paused
            self._update_tray_icon()
        elif cmd == ID_MENU_AUTOSTART:
            toggle_autostart()
        elif cmd == ID_MENU_TRIGGER_NOW:
            sound = self.config.get("sound_notification", False)
            threading.Thread(target=perform_correction, args=(sound,), daemon=True).start()
        elif cmd == ID_MENU_EXIT:
            self.stop()

    def open_settings_async(self):
        """Open settings dialog in separate thread."""
        threading.Thread(target=self._run_settings_gui, daemon=True).start()

    def _run_settings_gui(self):
        ensure_interactive_desktop()
        from settings_ui import open_settings_window
        open_settings_window(
            on_save_callback=self.apply_config,
            on_exit_callback=self.stop
        )

    def apply_config(self, new_config: dict):
        """Apply updated configuration dynamically without restarting."""
        self.config = new_config
        new_hotkey = new_config.get("hotkey", "F8")

        # Update hotkey if changed
        if new_hotkey != self.hotkey_str:
            user32.UnregisterHotKey(self.hwnd, ID_HOTKEY_MAIN)
            self.hotkey_str = new_hotkey
            self.vk, self.modifiers = parse_hotkey_string(self.hotkey_str)
            user32.RegisterHotKey(self.hwnd, ID_HOTKEY_MAIN, self.modifiers, self.vk)

        # Update tray icon presence
        if new_config.get("show_tray_icon", False):
            self._show_tray_icon()
        else:
            self._hide_tray_icon()

    def _wnd_proc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == WM_HOTKEY:
            if wparam == ID_HOTKEY_MAIN and not self.is_paused:
                sound = self.config.get("sound_notification", False)
                threading.Thread(target=perform_correction, args=(sound,), daemon=True).start()
            elif wparam == ID_HOTKEY_SETTINGS:
                self.open_settings_async()
            return 0

        elif msg == self.wm_show_settings:
            self.open_settings_async()
            return 0

        elif msg == self.wm_exit_app:
            self.stop()
            return 0

        elif msg == WM_TRAYICON:
            if lparam in (WM_RBUTTONUP, WM_CONTEXTMENU):
                self._show_context_menu()
            elif lparam == WM_LBUTTONUP:
                self.open_settings_async()
            return 0

        elif msg == WM_CLOSE:
            user32.DestroyWindow(hwnd)
            return 0

        elif msg == WM_DESTROY:
            self._cleanup_tray()
            user32.PostQuitMessage(0)
            return 0

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _cleanup_tray(self):
        if self.hwnd:
            self._hide_tray_icon()
            user32.UnregisterHotKey(self.hwnd, ID_HOTKEY_MAIN)
            user32.UnregisterHotKey(self.hwnd, ID_HOTKEY_SETTINGS)

    def start(self):
        """Create hidden worker window, register hotkeys, and run message loop."""
        ensure_interactive_desktop()
        self.thread_id = kernel32.GetCurrentThreadId()
        self._proc_delegate = WNDPROCTYPE(self._wnd_proc)

        wc = WNDCLASSW()
        wc.lpfnWndProc = self._proc_delegate
        wc.lpszClassName = self.class_name
        wc.hInstance = self.hinstance

        if not user32.RegisterClassW(ctypes.byref(wc)):
            raise RuntimeError("Failed to register window class")

        user32.ChangeWindowMessageFilter(self.wm_show_settings, 1)  # MSGFLT_ADD
        user32.ChangeWindowMessageFilter(self.wm_exit_app, 1)

        self.hwnd = user32.CreateWindowExW(
            0, self.class_name, self.window_title,
            0, 0, 0, 0, 0,
            None, None, self.hinstance, None
        )
        if not self.hwnd:
            user32.UnregisterClassW(self.class_name, self.hinstance)
            raise RuntimeError("Failed to create worker window")

        # 1. Register main layout correction hotkey
        res_main = user32.RegisterHotKey(self.hwnd, ID_HOTKEY_MAIN, self.modifiers, self.vk)
        if not res_main:
            print(f"Warning: Could not register main hotkey {self.hotkey_str} (VK={hex(self.vk)})")

        # 2. Register settings hotkey (Ctrl + Shift + F8 as quick fallback shortcut)
        user32.RegisterHotKey(self.hwnd, ID_HOTKEY_SETTINGS, MOD_NOREPEAT | MOD_CONTROL | MOD_SHIFT, VK_F8)

        # 3. Setup tray icon ONLY IF explicitly enabled in config (Default: False = stealth mode)
        if self.config.get("show_tray_icon", False):
            self._show_tray_icon()

        self.is_running = True

        # If launched with --settings, open settings GUI immediately
        if self.show_settings_on_start:
            self.open_settings_async()

        # Enter message loop
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        self.is_running = False
        user32.UnregisterClassW(self.class_name, self.hinstance)

    def stop(self):
        """Stop application cleanly from any thread."""
        if not self.is_running:
            return
        self.is_running = False
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
        elif self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)


def run_app():
    app = LayoutSwitcherTray()
    app.start()


if __name__ == "__main__":
    run_app()
