import pytest
import time
from win_api import (
    get_clipboard_text,
    set_clipboard_text,
    get_current_keyboard_layout,
    switch_system_layout,
    simulate_select_word,
    release_modifier_keys,
    HKL_HANDLE_RU,
    HKL_HANDLE_US,
)

def test_clipboard_operations():
    original = get_clipboard_text()
    test_str = "Тестовая строка для буфера обмена 123! @#"
    success = set_clipboard_text(test_str)
    assert success is True
    read_back = get_clipboard_text()
    assert read_back == test_str

    # Restore original if was present
    if original:
        set_clipboard_text(original)

def test_layout_handles():
    assert HKL_HANDLE_RU != 0
    assert HKL_HANDLE_US != 0

def test_layout_queries():
    lang = get_current_keyboard_layout()
    # May be 0 if running without interactive window, or 0x419 / 0x409
    assert isinstance(lang, int)

def test_safe_simulations():
    # Calling release_modifier_keys should not throw
    release_modifier_keys()

if __name__ == "__main__":
    pytest.main(["-v", __file__])
