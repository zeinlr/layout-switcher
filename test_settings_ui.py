import pytest
from settings_ui import SettingsWindow

def test_settings_initialization():
    win = SettingsWindow()
    assert win.config is not None
    assert "hotkey" in win.config
    assert win.current_hotkey != ""

if __name__ == "__main__":
    pytest.main(["-v", __file__])
