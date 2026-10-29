import pytest
from autostart import is_autostart_enabled, set_autostart, toggle_autostart

def test_autostart_toggle():
    original = is_autostart_enabled()

    # Enable
    res = set_autostart(True)
    assert res is True
    assert is_autostart_enabled() is True

    # Disable
    res = set_autostart(False)
    assert res is True
    assert is_autostart_enabled() is False

    # Restore original state
    set_autostart(original)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
