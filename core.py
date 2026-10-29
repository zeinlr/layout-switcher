"""
Core text replacement and layout switching coordinator.
"""

import time
from mapper import convert_text
from win_api import (
    ensure_interactive_desktop,
    get_clipboard_text,
    set_clipboard_text,
    get_current_keyboard_layout,
    switch_system_layout,
    simulate_copy,
    simulate_paste,
    simulate_select_word,
    release_modifier_keys,
)


def _wait_for_clipboard_text(max_wait_ms: int = 150) -> str:
    """Poll clipboard until it receives text or times out."""
    start = time.perf_counter()
    while (time.perf_counter() - start) * 1000 < max_wait_ms:
        txt = get_clipboard_text(timeout_ms=15)
        if txt:
            return txt
        time.sleep(0.01)
    return ""


def perform_correction(sound_enabled: bool = False) -> bool:
    """
    Executes the text layout conversion for active window:
    - Mode 1: Selected text.
    - Mode 2: Previous word if nothing selected.
    Returns True if text was converted and replaced.
    """
    ensure_interactive_desktop()
    release_modifier_keys()

    orig_clip = get_clipboard_text(timeout_ms=20)
    text_to_convert = ""

    # Step 1: Check if text is already selected (Mode 1)
    set_clipboard_text("")
    time.sleep(0.01)
    simulate_copy()
    copied = _wait_for_clipboard_text(max_wait_ms=100)

    if copied and copied.strip():
        text_to_convert = copied
    else:
        # Step 2: Nothing was selected -> Select last word (Mode 2)
        simulate_select_word()
        time.sleep(0.03)
        set_clipboard_text("")
        time.sleep(0.01)
        simulate_copy()
        copied = _wait_for_clipboard_text(max_wait_ms=100)
        if copied and copied.strip():
            text_to_convert = copied
        else:
            # Cannot get any text to convert; restore original clipboard
            if orig_clip:
                set_clipboard_text(orig_clip)
            return False

    if not text_to_convert:
        if orig_clip:
            set_clipboard_text(orig_clip)
        return False

    # Step 3: Determine layout and convert
    active_lang = get_current_keyboard_layout()
    is_ru = (active_lang == 0x0419)

    converted, target_dir = convert_text(text_to_convert, current_lang_is_ru=is_ru)
    if converted == text_to_convert:
        if orig_clip:
            set_clipboard_text(orig_clip)
        return False

    # Step 4: Paste converted text
    set_clipboard_text(converted)
    time.sleep(0.01)
    simulate_paste()
    time.sleep(0.02)

    # Step 5: Switch system keyboard layout to match the converted text
    switch_system_layout(to_ru=(target_dir == "to_ru"))
    if sound_enabled:
        from win_api import user32
        user32.MessageBeep(0)
    return True
