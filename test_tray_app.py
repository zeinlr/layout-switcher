import threading
import time
import pytest
from tray_app import LayoutSwitcherTray

def test_tray_lifecycle():
    app = LayoutSwitcherTray()
    thread = threading.Thread(target=app.start, daemon=True)
    thread.start()

    # Wait for app to initialize and run
    time.sleep(0.5)
    assert app.is_running is True
    assert app.hwnd is not None

    # Test pause toggle
    assert app.is_paused is False
    app.is_paused = True
    app._update_tray_icon()
    assert app.is_paused is True

    # Test clean stop
    app.stop()
    thread.join(timeout=2.0)
    assert not thread.is_alive()

if __name__ == "__main__":
    pytest.main(["-v", __file__])
