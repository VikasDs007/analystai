"""Lightweight Groq API sanity check.

This script reads the Groq API key from the project's Streamlit secrets or
environment, creates a Groq client, and issues a minimal chat completion to
verify connectivity.

It prints a short status line and exits with 0 on success, 2 on missing key,
and 3 on API call failure.
"""

import json
import pathlib
import re
import sys

from groq import Groq

from utils.helpers import _get_groq_api_key


def _read_key_from_secrets_file():
    root = pathlib.Path(__file__).resolve().parents[1]
    secrets_path = root / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        return ""

    text = secrets_path.read_text(encoding="utf-8")
    match = re.search(r'GROQ_API_KEY\s*=\s*"([^\"]+)"', text)
    if not match:
        match = re.search(r'GROQ_KEY\s*=\s*"([^\"]+)"', text)
    return match.group(1) if match else ""


KEY = _get_groq_api_key() or _read_key_from_secrets_file()
if not KEY:
    print("MISSING_KEY")
    sys.exit(2)

try:
    client = Groq(api_key=KEY)
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a connectivity tester."},
            {"role": "user", "content": "Say OK."},
        ],
        max_tokens=8,
        temperature=0.0,
    )
    text = resp.choices[0].message.content.strip()
    print("OK", json.dumps({"response": text}))
    sys.exit(0)
except Exception as exc:
    print("API_ERROR", str(exc))
    sys.exit(3)
