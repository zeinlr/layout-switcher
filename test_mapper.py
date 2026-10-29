import pytest
from mapper import convert_text, detect_direction, EN_TO_RU, RU_TO_EN

def test_en_to_ru():
    text = "ghbdtn"
    converted, direction = convert_text(text)
    assert direction == "to_ru"
    assert converted == "привет"

def test_ru_to_en():
    text = "руддщ"
    converted, direction = convert_text(text)
    assert direction == "to_en"
    assert converted == "hello"

def test_mixed_case():
    text = "Ghbdtn Vbh"
    converted, direction = convert_text(text)
    assert direction == "to_ru"
    assert converted == "Привет Мир"

    text2 = "Руддщ Цщкдв"
    converted2, direction2 = convert_text(text2)
    assert direction2 == "to_en"
    assert converted2 == "Hello World"

def test_punctuation_en_to_ru():
    # In EN layout:
    # '?' comes from Shift + '/' -> in RU that's ','
    # '/' is physical key -> in RU that's '.'
    # '@' -> '"'
    # '#' -> '№'
    # '$' -> ';'
    # '^' -> ':'
    # '&' -> '?'
    text = "Ghbdtn? rfr ltkf/ @ghjtrn# $100^ &xnj*"
    converted, _ = convert_text(text)
    assert converted == 'Привет, как дела. "проект№ ;100: ?что*'

def test_punctuation_ru_to_en():
    # In RU layout:
    # ',' comes from Shift + '/' -> in EN that's '?'
    # '.' comes from physical '/' -> in EN that's '/'
    # 'б' -> ','
    # 'ю' -> '.'
    # '"' -> '@'
    # '№' -> '#'
    # ';' -> '$'
    # ':' -> '^'
    # '?' -> '&'
    text = 'Руддщб цщкдв, "еуые№ ;200: ?н'
    converted, _ = convert_text(text)
    assert converted == 'Hello, world? @test# $200^ &y'

def test_empty():
    converted, _ = convert_text("")
    assert converted == ""

if __name__ == "__main__":
    pytest.main(["-v", __file__])
