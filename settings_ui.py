"""
Settings GUI for Layout Switcher.
Clean, modern, lightweight Tkinter interface.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from autostart import is_autostart_enabled, set_autostart
from config import load_config, save_config, get_config_dir
from win_api import ensure_interactive_desktop

PRESET_HOTKEYS = [
    "F8",
    "Pause",
    "Shift+CapsLock",
    "F9",
    "F11",
    "F12",
    "Ctrl+Shift+L",
    "Ctrl+Shift+F8",
]


class SettingsWindow:
    def __init__(self, on_save_callback=None, on_exit_callback=None):
        self.on_save_callback = on_save_callback
        self.on_exit_callback = on_exit_callback
        self.config_dir = get_config_dir()
        self.config = load_config(self.config_dir)

        self.root = None
        self.capturing_key = False
        self.current_hotkey = self.config.get("hotkey", "F8")

    def show(self):
        """Display the settings window. If already open, brings to foreground."""
        ensure_interactive_desktop()
        if self.root is not None and self.root.winfo_exists():
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self.root.lift()
            self.root.focus_force()
            self.root.after(100, lambda: self.root.attributes("-topmost", False))
            return

        self.root = tk.Tk()
        self.root.title("Layout Switcher — Настройки")
        self.root.geometry("450x430")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.after(200, lambda: self.root.attributes("-topmost", False) if self.root else None)

        # Set window icon if available
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self._center_window()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _center_window(self):
        self.root.update_idletasks()
        w = 450
        h = 430
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("vista")
        except Exception:
            pass

        main_frame = ttk.Frame(self.root, padding="16 16 16 16")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 14))

        title_lbl = ttk.Label(
            header_frame,
            text="Layout Switcher",
            font=("Segoe UI", 14, "bold")
        )
        title_lbl.pack(side=tk.LEFT)

        status_lbl = tk.Label(
            header_frame,
            text="● Активен в фоне",
            font=("Segoe UI", 9, "bold"),
            fg="#27ae60",
            bg=self.root.cget("bg")
        )
        status_lbl.pack(side=tk.RIGHT, pady=4)

        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 12))

        # Hotkey Group
        hotkey_group = ttk.LabelFrame(main_frame, text=" Горячая клавиша исправления ", padding="12 10 12 12")
        hotkey_group.pack(fill=tk.X, pady=(0, 12))

        hk_row = ttk.Frame(hotkey_group)
        hk_row.pack(fill=tk.X)

        ttk.Label(hk_row, text="Текущий хоткей:", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        self.hotkey_btn = tk.Button(
            hk_row,
            text=f" [ {self.current_hotkey} ] ",
            font=("Segoe UI", 9, "bold"),
            relief=tk.GROOVE,
            cursor="hand2",
            command=self._start_key_capture
        )
        self.hotkey_btn.pack(side=tk.RIGHT)

        preset_row = ttk.Frame(hotkey_group)
        preset_row.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(preset_row, text="Быстрый выбор:", font=("Segoe UI", 9)).pack(side=tk.LEFT)

        self.preset_combo = ttk.Combobox(
            preset_row,
            values=PRESET_HOTKEYS,
            state="readonly",
            width=16
        )
        if self.current_hotkey in PRESET_HOTKEYS:
            self.preset_combo.set(self.current_hotkey)
        else:
            self.preset_combo.set(PRESET_HOTKEYS[0])
        self.preset_combo.pack(side=tk.RIGHT)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_select)

        # Options Group
        opts_group = ttk.LabelFrame(main_frame, text=" Параметры работы ", padding="12 10 12 12")
        opts_group.pack(fill=tk.X, pady=(0, 14))

        self.var_autostart = tk.BooleanVar(value=is_autostart_enabled())
        chk_autostart = ttk.Checkbutton(
            opts_group,
            text="Запускать вместе с Windows (автозагрузка)",
            variable=self.var_autostart
        )
        chk_autostart.pack(anchor=tk.W, pady=3)

        self.var_tray = tk.BooleanVar(value=self.config.get("show_tray_icon", False))
        chk_tray = ttk.Checkbutton(
            opts_group,
            text="Отображать значок в системном трее",
            variable=self.var_tray
        )
        chk_tray.pack(anchor=tk.W, pady=3)

        self.var_sound = tk.BooleanVar(value=self.config.get("sound_notification", False))
        chk_sound = ttk.Checkbutton(
            opts_group,
            text="Звуковой сигнал при исправлении раскладки",
            variable=self.var_sound
        )
        chk_sound.pack(anchor=tk.W, pady=3)

        # Footer Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        exit_btn = tk.Button(
            btn_frame,
            text="Завершить работу",
            fg="#c0392b",
            font=("Segoe UI", 9),
            relief=tk.GROOVE,
            command=self._on_exit_app
        )
        exit_btn.pack(side=tk.LEFT)

        save_btn = ttk.Button(
            btn_frame,
            text="Сохранить и применить",
            command=self._save_and_apply
        )
        save_btn.pack(side=tk.RIGHT, padx=(6, 0))

        cancel_btn = ttk.Button(
            btn_frame,
            text="Закрыть",
            command=self._on_close
        )
        cancel_btn.pack(side=tk.RIGHT)

    def _start_key_capture(self):
        """Prompt user to press a key."""
        self.capturing_key = True
        self.hotkey_btn.config(text=" [ Нажмите клавишу... ] ", bg="#fff9c4")
        self.root.bind("<KeyPress>", self._on_key_press)

    def _on_key_press(self, event):
        if not self.capturing_key:
            return

        key = event.keysym.upper()
        # Filter modifier-only presses
        if key in ("SHIFT_L", "SHIFT_R", "CONTROL_L", "CONTROL_R", "ALT_L", "ALT_R", "WIN_L", "WIN_R"):
            return

        # Friendly key names
        key_name = key
        if key == "CAPS_LOCK":
            key_name = "CapsLock"
        elif key.startswith("F") and len(key) in (2, 3) and key[1:].isdigit():
            key_name = key
        elif key == "PAUSE":
            key_name = "Pause"

        # Check modifiers
        mods = []
        if event.state & 0x0004:  # Control
            mods.append("Ctrl")
        if event.state & 0x0001:  # Shift
            mods.append("Shift")
        if event.state & 0x0008:  # Alt
            mods.append("Alt")

        if mods:
            hotkey_str = "+".join(mods + [key_name])
        else:
            hotkey_str = key_name

        self.current_hotkey = hotkey_str
        self.hotkey_btn.config(text=f" [ {self.current_hotkey} ] ", bg=self.root.cget("bg"))
        if self.current_hotkey in PRESET_HOTKEYS:
            self.preset_combo.set(self.current_hotkey)
        else:
            self.preset_combo.set("")

        self.capturing_key = False
        self.root.unbind("<KeyPress>")

    def _on_preset_select(self, event):
        val = self.preset_combo.get()
        if val:
            self.current_hotkey = val
            self.hotkey_btn.config(text=f" [ {self.current_hotkey} ] ")

    def _save_and_apply(self):
        # Update config dict
        self.config["hotkey"] = self.current_hotkey
        self.config["show_tray_icon"] = self.var_tray.get()
        self.config["sound_notification"] = self.var_sound.get()

        # Save to config.json
        save_config(self.config, self.config_dir)

        # Update Windows autostart
        set_autostart(self.var_autostart.get())

        # Notify callback in background worker if running
        if self.on_save_callback:
            try:
                self.on_save_callback(self.config)
            except Exception:
                pass

        messagebox.showinfo("Layout Switcher", "Настройки успешно сохранены и применены!")
        self._on_close()

    def _on_exit_app(self):
        if messagebox.askyesno("Layout Switcher", "Вы действительно хотите завершить работу утилиты?"):
            if self.on_exit_callback:
                try:
                    self.on_exit_callback()
                except Exception:
                    pass
            self._on_close()

    def _on_close(self):
        if self.root:
            self.root.destroy()
            self.root = None


def open_settings_window(on_save_callback=None, on_exit_callback=None):
    win = SettingsWindow(on_save_callback, on_exit_callback)
    win.show()


if __name__ == "__main__":
    open_settings_window()
