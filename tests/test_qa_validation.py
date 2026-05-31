import pytest
from utils.helpers import validate_user_question


def test_validate_accepts_simple_question():
    txt = "Which region has the highest sales?"
    cleaned = validate_user_question(txt)
    assert "region" in cleaned.lower()


def test_validate_rejects_empty():
    with pytest.raises(ValueError):
        validate_user_question("")


def test_validate_rejects_long():
    longq = "x" * 1000
    with pytest.raises(ValueError):
        validate_user_question(longq, max_len=500)


def test_validate_rejects_email():
    with pytest.raises(ValueError):
        validate_user_question("Please contact me at test@example.com")


def test_validate_rejects_phone():
    with pytest.raises(ValueError):
        validate_user_question("Call 123-456-7890")


def test_validate_rejects_profanity():
    with pytest.raises(ValueError):
        validate_user_question("This is shit")
