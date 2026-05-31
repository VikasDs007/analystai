"""Shared utilities for AnalystAI agents."""

import json
import os
import re
from types import SimpleNamespace

import requests
import streamlit as st


def validate_user_question(text: str, *, max_len: int = 800):
    """Validate and sanitize a user-supplied question.

    Raises ValueError with a user-friendly message when validation fails.
    Returns the cleaned text when valid.
    """
    if text is None:
        raise ValueError("Question is empty")
    txt = str(text).strip()
    if not txt:
        raise ValueError("Please enter a question.")

    if len(txt) > max_len:
        raise ValueError(f"Question is too long ({len(txt)} characters). Please shorten to under {max_len} characters.")

    # Basic PII filters
    # Emails
    if re.search(r"[\w.-]+@[\w.-]+\.[a-zA-Z]{2,}", txt):
        raise ValueError("Please remove email addresses from your question for privacy.")
    # Phone numbers (simple patterns)
    if re.search(r"\b\d{10,}\b", re.sub(r"[^0-9]", "", txt)):
        raise ValueError("Please remove phone numbers from your question for privacy.")

    # Profanity: minimal list to avoid offensive content
    profane = {"shit", "fuck", "damn", "bitch"}
    low = txt.lower()
    for p in profane:
        if re.search(rf"\b{re.escape(p)}\b", low):
            raise ValueError("Please avoid profanity in your question.")

    # Remove CSS-like selector lines or style blocks accidentally pasted
    txt = re.sub(r'(?m)^[A-Za-z0-9_\.\-]+\s*\{[^}]*\}\s*$', '', txt)
    txt = re.sub(r'(?is)<style.*?>.*?</style>', '', txt)

    # Normalize whitespace
    txt = re.sub(r"\s{2,}", " ", txt)

    return txt


_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_OPENROUTER_MODEL = "openai/gpt-oss-120b:free"


def _secret_value(*names):
    try:
        for secret_name in names:
            value = st.secrets.get(secret_name, "") or ""
            if value:
                return value
    except Exception:
        pass

    for env_name in names:
        value = os.environ.get(env_name, "") or ""
        if value:
            return value
    return ""


# ── OpenRouter client ─────────────────────────────────────────────────────────

def get_api_key():
    """Return the configured OpenRouter API key."""
    return _secret_value("OPEN_ROUTER_KEY", "OPENROUTER_API_KEY")


def has_api_key():
    """Return True when an OpenRouter API key is configured."""
    return bool(get_api_key())


# Keep legacy names so any remaining call-sites don't break at import time
has_groq_api_key = has_api_key


def use_full_ai():
    """Always True — the app is AI-only; no local fallback mode."""
    return True


class _Completions:
    def __init__(self, api_key, timeout=30.0):
        self._api_key = api_key
        self._timeout = timeout

    def create(self, **kwargs):
        stream = bool(kwargs.get("stream", False))
        payload = {k: v for k, v in kwargs.items() if k not in {"timeout", "max_retries"}}
        # Always use the configured OpenRouter model
        payload["model"] = _OPENROUTER_MODEL

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        if stream:
            return self._stream_chat(payload, headers)

        resp = requests.post(
            _OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=self._timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        message = (data.get("choices") or [{}])[0].get("message") or {}
        content = message.get("content") or ""
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )

    def _stream_chat(self, payload, headers):
        def _iter():
            p = dict(payload)
            p["stream"] = True
            with requests.post(
                _OPENROUTER_URL,
                headers=headers,
                json=p,
                timeout=self._timeout,
                stream=True,
            ) as resp:
                resp.raise_for_status()
                for raw_line in resp.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    line = raw_line.strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except Exception:
                        continue
                    choice = (chunk.get("choices") or [{}])[0]
                    delta = ""
                    if isinstance(choice.get("delta"), dict):
                        delta = choice["delta"].get("content") or ""
                    elif isinstance(choice.get("message"), dict):
                        delta = choice["message"].get("content") or ""
                    if delta:
                        yield SimpleNamespace(
                            choices=[SimpleNamespace(delta=SimpleNamespace(content=delta))]
                        )

        return _iter()


class _OpenRouterClient:
    def __init__(self, api_key, timeout=30.0):
        self.chat = SimpleNamespace(completions=_Completions(api_key, timeout=timeout))


def get_llm_client(*, timeout=30.0):
    """Return an OpenAI client. Raises ValueError if no API key is set."""
    key = get_api_key()
    if not key:
        raise ValueError(
            "OpenAI API key not found. "
            "Add OPEN_ROUTER_KEY to .streamlit/secrets.toml or your environment."
        )
    return _OpenRouterClient(key, timeout=timeout)


# Legacy alias used across agents
get_groq_client = get_llm_client


def get_llm_provider_name():
    return "OpenAI" if has_api_key() else ""


def llm_json_decision(system_prompt, user_prompt, *,
                      max_tokens=900, temperature=0.1, timeout=30.0):
    """Ask the LLM for a JSON decision and return a parsed dict.

    Returns None when the API is unavailable or the payload cannot be parsed.
    """
    try:
        client = get_llm_client(timeout=timeout)
        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception:
        return None


# Legacy alias
groq_json_decision = llm_json_decision


# ── Column-type helpers ───────────────────────────────────────────────────────

def is_identifier_col(col):
    name = col.lower()
    return (name == "id" or name.endswith("_id") or
            "order_id" in name or "serial" in name or name == "index")


def choose_main_numeric(numeric_cols):
    candidates = [c for c in numeric_cols if not is_identifier_col(c)]
    if not candidates:
        return numeric_cols[0] if numeric_cols else None
    preferred = ["total_sales", "sales", "revenue", "profit", "amount",
                 "price", "quantity", "total", "value", "income"]
    for term in preferred:
        for col in candidates:
            if term in col.lower():
                return col
    return candidates[0]


def choose_main_category(cat_cols):
    if not cat_cols:
        return None
    preferred = ["category", "product", "region", "city", "segment",
                 "channel", "payment", "mode", "type", "status"]
    for term in preferred:
        for col in cat_cols:
            if term in col.lower():
                return col
    return cat_cols[0]


# ── Business KPI computation ──────────────────────────────────────────────────

def compute_business_kpis(df):
    """Auto-detect and compute business KPIs from a cleaned dataframe."""
    import numpy as np

    numeric = [c for c in df.select_dtypes(include=[np.number]).columns
               if not is_identifier_col(c)]

    kpis = []

    revenue_col = choose_main_numeric(numeric)
    if revenue_col:
        total = df[revenue_col].sum()
        avg   = df[revenue_col].mean()
        # Find top category for this metric
        cat_cols = [c for c in df.select_dtypes(include=["object"]).columns
                    if df[c].nunique() <= 20 and not is_identifier_col(c)]
        main_cat = choose_main_category(cat_cols)
        if main_cat and main_cat in df.columns:
            top_cat = df.groupby(main_cat)[revenue_col].sum().idxmax()
            sub = f"top: {str(top_cat)[:18]}"
        else:
            sub = f"avg {_fmt_number(avg)} per record"
        kpis.append({
            "label": revenue_col.replace("_", " ").title(),
            "value": _fmt_number(total),
            "sub":   sub,
            "color": "kpi-blue",
            "icon":  "💰",
        })

    profit_col = next((c for c in numeric if "profit" in c.lower()), None)
    if profit_col and revenue_col and profit_col != revenue_col:
        total_profit  = df[profit_col].sum()
        total_revenue = df[revenue_col].sum()
        margin = (total_profit / total_revenue * 100) if total_revenue else 0
        kpis.append({
            "label": "Profit Margin",
            "value": f"{margin:.1f}%",
            "sub":   f"total profit {_fmt_number(total_profit)}",
            "color": "kpi-green",
            "icon":  "📈",
        })
    elif profit_col:
        avg_p = df[profit_col].mean()
        kpis.append({
            "label": profit_col.replace("_", " ").title(),
            "value": _fmt_number(df[profit_col].sum()),
            "sub":   f"avg {_fmt_number(avg_p)} per record",
            "color": "kpi-green",
            "icon":  "📈",
        })

    kpis.append({
        "label": "Total Records",
        "value": f"{len(df):,}",
        "sub":   f"{df.shape[1]} columns",
        "color": "kpi-purple",
        "icon":  "📋",
    })

    qty_col = next((c for c in numeric
                    if "qty" in c.lower() or "quantity" in c.lower()
                    or "units" in c.lower() or "count" in c.lower()), None)
    if qty_col:
        total_qty = int(df[qty_col].sum())
        avg_qty = df[qty_col].mean()
        kpis.append({
            "label": qty_col.replace("_", " ").title(),
            "value": f"{total_qty:,}",
            "sub":   f"avg {avg_qty:.1f} per order",
            "color": "kpi-amber",
            "icon":  "📦",
        })

    disc_col = next((c for c in numeric
                     if "discount" in c.lower() or "rate" in c.lower()
                     or "pct" in c.lower() or "percent" in c.lower()), None)
    if disc_col and len(kpis) < 6:
        avg_disc = df[disc_col].mean()
        max_disc = df[disc_col].max()
        kpis.append({
            "label": disc_col.replace("_", " ").title(),
            "value": f"{avg_disc:.1f}%",
            "sub":   f"max {max_disc:.1f}% · avg across {len(df):,} records",
            "color": "kpi-rose",
            "icon":  "🏷️",
        })

    for col in numeric:
        if len(kpis) >= 6:
            break
        if col in [revenue_col, profit_col, qty_col, disc_col]:
            continue
        kpis.append({
            "label": col.replace("_", " ").title(),
            "value": _fmt_number(df[col].sum()),
            "sub":   f"avg {_fmt_number(df[col].mean())}",
            "color": "kpi-purple",
            "icon":  "📊",
        })

    return kpis[:6]


def _fmt_number(n):
    try:
        n = float(n)
    except Exception:
        return str(n)
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:
        return f"{n/1_000:.1f}K"
    return f"{n:,.1f}"


# ── Column type badge ─────────────────────────────────────────────────────────

def col_type_badge(dtype_str, col_name):
    if is_identifier_col(col_name):
        return '<span style="background:#F1F5F9;color:#64748B;padding:2px 8px;border-radius:10px;font-size:0.72rem;font-weight:600;">ID</span>'
    name = col_name.lower()
    if "date" in name or "time" in name:
        return '<span style="background:#FEF3C7;color:#D97706;padding:2px 8px;border-radius:10px;font-size:0.72rem;font-weight:600;">📅 DATE</span>'
    if "int" in dtype_str or "float" in dtype_str:
        return '<span style="background:#DBEAFE;color:#1D4ED8;padding:2px 8px;border-radius:10px;font-size:0.72rem;font-weight:600;">🔢 NUM</span>'
    return '<span style="background:#F0FDF4;color:#16A34A;padding:2px 8px;border-radius:10px;font-size:0.72rem;font-weight:600;">🔤 TEXT</span>'


# ── Markdown → safe HTML ──────────────────────────────────────────────────────

def md_to_html(text):
    if not text:
        return ""

    # Fix common mojibake (double-decoded UTF-8) so emojis and dashes render correctly.
    try:
        text = fix_mojibake(text)
    except Exception:
        pass

    lines = text.split("\n")
    out = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("### "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f'<h4 style="color:#1E293B;font-weight:600;margin:1rem 0 0.4rem 0;">{stripped[4:]}</h4>')
            continue
        if stripped.startswith("## "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f'<h3 style="color:#1E293B;font-weight:700;margin:1.2rem 0 0.5rem 0;">{stripped[3:]}</h3>')
            continue
        if stripped.startswith("# "):
            if in_list:
                out.append("</ul>"); in_list = False
            out.append(f'<h2 style="color:#1E293B;font-weight:700;margin:1.2rem 0 0.5rem 0;">{stripped[2:]}</h2>')
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                out.append('<ul style="margin:0.4rem 0 0.4rem 1.2rem;padding:0;">')
                in_list = True
            item = _inline_md(stripped[2:])
            out.append(f'<li style="margin-bottom:4px;color:#374151;">{item}</li>')
            continue

        if in_list and stripped:
            out.append("</ul>")
            in_list = False

        if not stripped:
            out.append('<div style="height:6px;"></div>')
            continue

        out.append(f'<p style="margin:0 0 6px 0;color:#374151;line-height:1.65;">{_inline_md(stripped)}</p>')

    if in_list:
        out.append("</ul>")

    return "\n".join(out)


def _inline_md(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code style="background:#F1F5F9;padding:1px 5px;border-radius:3px;font-size:0.88em;">\1</code>', text)
    return text


def fix_mojibake(text: str) -> str:
    """Attempt to repair common UTF-8/LATIN-1 mojibake sequences.

    Many LLMs and external sources may produce strings that were decoded
    with the wrong encoding (UTF-8 bytes interpreted as latin-1). This
    helper tries a safe round-trip conversion: encode as latin-1 and
    decode as UTF-8. If that fails or doesn't improve the string, the
    original text is returned.
    """
    if not isinstance(text, str) or not text:
        return text
    # Fast check: common mojibake markers
    markers = ["Ã", "â", "ð", "Â", "â" ]
    if not any(m in text for m in markers):
        return text

    try:
        # Try to recover by interpreting current str as latin-1 bytes
        # then decoding as utf-8. This fixes sequences like â -> –
        recovered = text.encode('latin-1').decode('utf-8')
        return recovered
    except Exception:
        return text


# ── Suggested Q&A questions ───────────────────────────────────────────────────

def suggest_questions(df):
    import numpy as np

    numeric = [c for c in df.select_dtypes(include=[np.number]).columns
               if not is_identifier_col(c)]
    categorical = [c for c in df.select_dtypes(include=["object"]).columns
                   if df[c].nunique() <= 30 and not is_identifier_col(c)]

    main_num = choose_main_numeric(numeric)
    main_cat = choose_main_category(categorical)

    questions = []
    if main_num and main_cat:
        questions.append(f"Which {main_cat.replace('_',' ')} has the highest {main_num.replace('_',' ')}?")
        questions.append(f"What is the total {main_num.replace('_',' ')}?")

    profit_col = next((c for c in numeric if "profit" in c.lower()), None)
    if profit_col:
        questions.append(f"What is the average {profit_col.replace('_',' ')}?")
        if main_cat:
            questions.append(f"Which {main_cat.replace('_',' ')} is most profitable?")

    region_col = next((c for c in categorical if "region" in c.lower()), None)
    if region_col:
        questions.append(f"Which {region_col.replace('_',' ')} is underperforming?")

    disc_col = next((c for c in numeric if "discount" in c.lower()), None)
    if disc_col and profit_col:
        questions.append("Does giving discounts hurt profit?")

    sec_cat = next((c for c in categorical
                    if c != main_cat and ("rep" in c.lower() or "product" in c.lower())), None)
    if sec_cat and main_num:
        questions.append(f"Who are the top 3 {sec_cat.replace('_',' ')}s by {main_num.replace('_',' ')}?")

    seen = set()
    unique = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique[:4]


# ── Data-summary builder ──────────────────────────────────────────────────────

def build_data_context(df, understanding=""):
    import numpy as np

    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns
                    if not is_identifier_col(c)]
    cat_cols = [c for c in df.select_dtypes(include=["object"]).columns
                if df[c].nunique() <= 30]

    main_num = choose_main_numeric(numeric_cols)

    num_lines = []
    for col in numeric_cols[:8]:
        num_lines.append(
            f"  {col}: total={df[col].sum():,.2f}, avg={df[col].mean():,.2f}, "
            f"max={df[col].max():,.2f}, min={df[col].min():,.2f}"
        )

    cat_lines = []
    for col in cat_cols[:6]:
        if main_num:
            top = df.groupby(col)[main_num].sum().sort_values(ascending=False).head(5)
            rows = ", ".join(f"{k}: {v:,.0f}" for k, v in top.items())
        else:
            vc = df[col].value_counts().head(5)
            rows = ", ".join(f"{k}: {v}" for k, v in vc.items())
        cat_lines.append(f"  {col} → {rows}")

    return "\n".join([
        f"Dataset overview: {understanding}",
        f"Total records: {len(df)}",
        f"Columns: {', '.join(df.columns.tolist())}",
        "",
        "NUMERIC SUMMARIES (total / avg / max / min):",
        "\n".join(num_lines) if num_lines else "  None",
        "",
        "CATEGORY BREAKDOWNS (ranked by main metric):",
        "\n".join(cat_lines) if cat_lines else "  None",
        "",
        "SAMPLE ROWS (first 5):",
        df.head(5).to_string(),
    ])
