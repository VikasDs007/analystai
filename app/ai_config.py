"""AI configuration — OpenAI powered, always-on AI mode."""

from utils.helpers import has_api_key, get_api_key


def has_groq_api_key():
    """Legacy alias — returns True when an OpenAI API key is configured."""
    return has_api_key()


def use_full_ai():
    """Always True — the app requires an API key and has no local fallback."""
    return True


def get_ai_mode():
    """Always returns 'api_key' — local mode has been removed."""
    return "api_key"
