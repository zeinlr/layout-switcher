"""
Windows API bindings and helper functions via ctypes.
Optimized for 64-bit Windows, minimal RAM and high reliability.
"""

import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
shell32 = ctypes.windll.shell32

# Types
LRESULT = ctypes.c_int64
PUL = ctypes.c_size_t

# Constants
CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

WM_HOTKEY = 0x0312
WM_USER = 0x0400
WM_TRAYICON = WM_USER + 1
WM_INPUTLANGCHANGEREQUEST = 0x0050
WM_COMMAND = 0x0111
WM_RBUTTONUP = 0x0205
WM_LBUTTONUP = 0x0202
WM_CONTEXTMENU = 0x007B
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
WM_QUIT = 0x0012

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_LEFT = 0x25
VK_C = 0x43
VK_V = 0x56
VK_F8 = 0x77
VK_PAUSE = 0x13
VK_CAPITAL = 0x14

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

# Keyboard layouts
HKL_US = 0x04090409
HKL_RU = 0x04190419

# Structures
class KeyBdInput(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", PUL),
    ]

class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", PUL),
    ]

class HardwareInput(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]

class Input_I(ctypes.Union):
    _fields_ = [
        ("ki", KeyBdInput),
        ("mi", MouseInput),
        ("hi", HardwareInput),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("ii", Input_I),
    ]

class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    ]

class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", ctypes.c_byte * 16),
        ("hBalloonIcon", wintypes.HICON),
    ]

WNDPROCTYPE = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROCTYPE),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HICON),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]

# Setup Win32 function signatures
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE

kernel32.GetCurrentThreadId.argtypes = []
kernel32.GetCurrentThreadId.restype = wintypes.DWORD

user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.PostQuitMessage.restype = None

user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostThreadMessageW.restype = wintypes.BOOL

user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.DefWindowProcW.restype = LRESULT

user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = wintypes.ATOM

user32.UnregisterClassW.argtypes = [wintypes.LPCWSTR, wintypes.HINSTANCE]
user32.UnregisterClassW.restype = wintypes.BOOL

user32.CreateWindowExW.argtypes = [
    wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
    wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
]
user32.CreateWindowExW.restype = wintypes.HWND

user32.DestroyWindow.argtypes = [wintypes.HWND]
user32.DestroyWindow.restype = wintypes.BOOL

user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.RegisterHotKey.restype = wintypes.BOOL

user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL

user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT

user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL

user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL

user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = wintypes.BOOL

user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE

user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL

kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = ctypes.c_void_p

kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL

user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND

user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD

user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
user32.GetKeyboardLayout.restype = wintypes.HKL

user32.LoadKeyboardLayoutW.argtypes = [wintypes.LPCWSTR, wintypes.UINT]
user32.LoadKeyboardLayoutW.restype = wintypes.HKL

user32.ActivateKeyboardLayout.argtypes = [wintypes.HKL, wintypes.UINT]
user32.ActivateKeyboardLayout.restype = wintypes.HKL

user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
user32.MapVirtualKeyW.restype = wintypes.UINT

user32.OpenWindowStationW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL, wintypes.DWORD]
user32.OpenWindowStationW.restype = wintypes.HANDLE

user32.SetProcessWindowStation.argtypes = [wintypes.HANDLE]
user32.SetProcessWindowStation.restype = wintypes.BOOL

user32.OpenDesktopW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
user32.OpenDesktopW.restype = wintypes.HANDLE

user32.SetThreadDesktop.argtypes = [wintypes.HANDLE]
user32.SetThreadDesktop.restype = wintypes.BOOL

user32.MessageBeep.argtypes = [wintypes.UINT]
user32.MessageBeep.restype = wintypes.BOOL

user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL

user32.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(GUITHREADINFO)]
user32.GetGUIThreadInfo.restype = wintypes.BOOL

user32.CreatePopupMenu.argtypes = []
user32.CreatePopupMenu.restype = wintypes.HMENU

user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
user32.AppendMenuW.restype = wintypes.BOOL

user32.TrackPopupMenuEx.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.HWND, ctypes.c_void_p]
user32.TrackPopupMenuEx.restype = wintypes.BOOL

user32.DestroyMenu.argtypes = [wintypes.HMENU]
user32.DestroyMenu.restype = wintypes.BOOL

user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
user32.GetCursorPos.restype = wintypes.BOOL

user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL

shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
shell32.Shell_NotifyIconW.restype = wintypes.BOOL


# Preload keyboard layout handles
HKL_HANDLE_RU = user32.LoadKeyboardLayoutW("00000419", 1) or HKL_RU
HKL_HANDLE_US = user32.LoadKeyboardLayoutW("00000409", 1) or HKL_US


def ensure_interactive_desktop():
    """Attach current thread and process to interactive user desktop (WinSta0\\Default)."""
    try:
        h_winsta = user32.OpenWindowStationW("WinSta0", False, 0x10000000)
        if h_winsta:
            user32.SetProcessWindowStation(h_winsta)
        h_desk = user32.OpenDesktopW("Default", 0, False, 0x10000000)
        if h_desk:
            user32.SetThreadDesktop(h_desk)
    except Exception:
        pass


def get_clipboard_text(timeout_ms: int = 150) -> str:
    """Read UTF-16 text from the Windows clipboard safely."""
    start_time = time.perf_counter()
    while (time.perf_counter() - start_time) * 1000 < timeout_ms:
        if user32.OpenClipboard(None):
            try:
                h_mem = user32.GetClipboardData(CF_UNICODETEXT)
                if not h_mem:
                    return ""
                ptr = kernel32.GlobalLock(h_mem)
                if not ptr:
                    return ""
                try:
                    return ctypes.wstring_at(ptr)
                finally:
                    kernel32.GlobalUnlock(h_mem)
            finally:
                user32.CloseClipboard()
        time.sleep(0.01)
    return ""


def set_clipboard_text(text: str, timeout_ms: int = 150) -> bool:
    """Set UTF-16 text into the Windows clipboard safely."""
    encoded = text.encode("utf-16le") + b"\x00\x00"
    h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
    if not h_mem:
        return False

    ptr = kernel32.GlobalLock(h_mem)
    if not ptr:
        return False
    ctypes.memmove(ptr, encoded, len(encoded))
    kernel32.GlobalUnlock(h_mem)

    start_time = time.perf_counter()
    while (time.perf_counter() - start_time) * 1000 < timeout_ms:
        if user32.OpenClipboard(None):
            try:
                user32.EmptyClipboard()
                res = user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                return bool(res)
            finally:
                user32.CloseClipboard()
        time.sleep(0.01)
    return False


def _make_key_input(vk: int, up: bool = False, extended: bool = False) -> INPUT:
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    flags = 0
    if up:
        flags |= KEYEVENTF_KEYUP
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    inp.ii.ki.wVk = vk
    inp.ii.ki.wScan = user32.MapVirtualKeyW(vk, 0)
    inp.ii.ki.dwFlags = flags
    inp.ii.ki.time = 0
    inp.ii.ki.dwExtraInfo = 0
    return inp


def send_inputs(inputs: list[INPUT]):
    """Send array of keyboard events."""
    if not inputs:
        return
    n = len(inputs)
    arr = (INPUT * n)(*inputs)
    user32.SendInput(n, arr, ctypes.sizeof(INPUT))


def release_modifier_keys():
    """Ensure modifier keys (Shift, Ctrl, Alt, Win) are released."""
    keys_to_release = [VK_SHIFT, VK_CONTROL, VK_MENU, VK_LWIN, VK_RWIN]
    inputs = []
    for vk in keys_to_release:
        if user32.GetAsyncKeyState(vk) & 0x8000:
            inputs.append(_make_key_input(vk, up=True))
    if inputs:
        send_inputs(inputs)
        time.sleep(0.01)


def simulate_copy():
    """Simulate Ctrl+C to copy selected text."""
    release_modifier_keys()
    inputs = [
        _make_key_input(VK_CONTROL, up=False),
        _make_key_input(VK_C, up=False),
        _make_key_input(VK_C, up=True),
        _make_key_input(VK_CONTROL, up=True),
    ]
    send_inputs(inputs)


def simulate_paste():
    """Simulate Ctrl+V to paste converted text."""
    release_modifier_keys()
    inputs = [
        _make_key_input(VK_CONTROL, up=False),
        _make_key_input(VK_V, up=False),
        _make_key_input(VK_V, up=True),
        _make_key_input(VK_CONTROL, up=True),
    ]
    send_inputs(inputs)


def simulate_select_word():
    """Simulate Ctrl+Shift+Left to select previous word."""
    release_modifier_keys()
    inputs = [
        _make_key_input(VK_CONTROL, up=False),
        _make_key_input(VK_SHIFT, up=False),
        _make_key_input(VK_LEFT, up=False, extended=True),
        _make_key_input(VK_LEFT, up=True, extended=True),
        _make_key_input(VK_SHIFT, up=True),
        _make_key_input(VK_CONTROL, up=True),
    ]
    send_inputs(inputs)


def get_active_target_windows() -> tuple[wintypes.HWND, wintypes.HWND]:
    """
    Returns (foreground_hwnd, focused_hwnd).
    """
    fg_hwnd = user32.GetForegroundWindow()
    focused_hwnd = None
    if fg_hwnd:
        tid = user32.GetWindowThreadProcessId(fg_hwnd, None)
        gui_info = GUITHREADINFO()
        gui_info.cbSize = ctypes.sizeof(GUITHREADINFO)
        if user32.GetGUIThreadInfo(tid, ctypes.byref(gui_info)):
            focused_hwnd = gui_info.hwndFocus or gui_info.hwndActive
    return fg_hwnd, (focused_hwnd or fg_hwnd)


def get_current_keyboard_layout() -> int:
    """Return LangID of active thread/window (0x419 for RU, 0x409 for EN)."""
    fg_hwnd = user32.GetForegroundWindow()
    if not fg_hwnd:
        return 0
    tid = user32.GetWindowThreadProcessId(fg_hwnd, None)
    hkl = user32.GetKeyboardLayout(tid)
    return hkl & 0xFFFF


def switch_system_layout(to_ru: bool):
    """
    Switch active window layout to RU or EN.
    Uses PostMessageW WM_INPUTLANGCHANGEREQUEST and ActivateKeyboardLayout.
    """
    target_hkl = HKL_HANDLE_RU if to_ru else HKL_HANDLE_US
    fg_hwnd, focused_hwnd = get_active_target_windows()

    for hwnd in {fg_hwnd, focused_hwnd}:
        if hwnd:
            user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, target_hkl)
    user32.ActivateKeyboardLayout(target_hkl, 0)
