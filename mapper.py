"""
Keyboard layout mapper for Russian <-> English (QWERTY <-> JCUKEN).
"""

# EN -> RU mapping
EN_TO_RU = {
    # Lowercase letters & keys
    '`': 'ё', 'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н',
    'u': 'г', 'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ',
    'a': 'ф', 's': 'ы', 'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р',
    'j': 'о', 'k': 'л', 'l': 'д', ';': 'ж', "'": 'э',
    'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и', 'n': 'т',
    'm': 'ь', ',': 'б', '.': 'ю', '/': '.',

    # Uppercase letters & shifted keys
    '~': 'Ё', 'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н',
    'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З', '{': 'Х', '}': 'Ъ',
    'A': 'Ф', 'S': 'Ы', 'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р',
    'J': 'О', 'K': 'Л', 'L': 'Д', ':': 'Ж', '"': 'Э',
    'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И', 'N': 'Т',
    'M': 'Ь', '<': 'Б', '>': 'Ю', '?': ',',

    # Shifted number row / special
    '@': '"', '#': '№', '$': ';', '^': ':', '&': '?', '|': '/'
}

# RU -> EN mapping
RU_TO_EN = {
    # Lowercase letters & keys
    'ё': '`', 'й': 'q', 'ц': 'w', 'у': 'e', 'к': 'r', 'е': 't', 'н': 'y',
    'г': 'u', 'ш': 'i', 'щ': 'o', 'з': 'p', 'х': '[', 'ъ': ']',
    'ф': 'a', 'ы': 's', 'в': 'd', 'а': 'f', 'п': 'g', 'р': 'h',
    'о': 'j', 'л': 'k', 'д': 'l', 'ж': ';', 'э': "'",
    'я': 'z', 'ч': 'x', 'с': 'c', 'м': 'v', 'и': 'b', 'т': 'n',
    'ь': 'm', 'б': ',', 'ю': '.', '.': '/',

    # Uppercase letters & shifted keys
    'Ё': '~', 'Й': 'Q', 'Ц': 'W', 'У': 'E', 'К': 'R', 'Е': 'T', 'Н': 'Y',
    'Г': 'U', 'Ш': 'I', 'Щ': 'O', 'З': 'P', 'Х': '{', 'Ъ': '}',
    'Ф': 'A', 'Ы': 'S', 'В': 'D', 'А': 'F', 'П': 'G', 'Р': 'H',
    'О': 'J', 'Л': 'K', 'Д': 'L', 'Ж': ':', 'Э': '"',
    'Я': 'Z', 'Ч': 'X', 'С': 'C', 'М': 'V', 'И': 'B', 'Т': 'N',
    'Ь': 'M', 'Б': '<', 'Ю': '>', ',': '?',

    # Shifted number row / special
    '"': '@', '№': '#', ';': '$', ':': '^', '?': '&', '/': '|'
}

RU_CHARS = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ№")
EN_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@#$^&")


def detect_direction(text: str, default_to_ru: bool = True) -> str:
    """
    Detect whether text should be converted to RU or to EN.
    Returns 'to_ru' or 'to_en'.
    """
    ru_count = sum(1 for c in text if c in RU_CHARS)
    en_count = sum(1 for c in text if c in EN_CHARS)

    if ru_count > en_count:
        return 'to_en'
    elif en_count > ru_count:
        return 'to_ru'
    else:
        # Check specific symbols if no letters
        if any(c in '№' for c in text):
            return 'to_en'
        if any(c in '@#$^&' for c in text):
            return 'to_ru'
        return 'to_ru' if default_to_ru else 'to_en'


def convert_text(text: str, force_direction: str | None = None, current_lang_is_ru: bool = False) -> tuple[str, str]:
    """
    Convert text from EN to RU or RU to EN.
    Returns: (converted_text, target_direction: 'to_ru' | 'to_en')
    """
    if not text:
        return text, 'to_ru'

    if force_direction in ('to_ru', 'to_en'):
        direction = force_direction
    else:
        # If ambiguous, use current_lang_is_ru (if active layout is RU, user probably mistyped in RU -> to_en)
        direction = detect_direction(text, default_to_ru=not current_lang_is_ru)

    mapping = EN_TO_RU if direction == 'to_ru' else RU_TO_EN
    result = ''.join(mapping.get(c, c) for c in text)
    return result, direction
