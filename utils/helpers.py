"""Shared utilities for AnalystAI agents."""

import json
import os
import re
import streamlit as st
from groq import Groq


# ── Groq client ───────────────────────────────────────────────────────────────

def get_groq_client():
    key = _get_groq_api_key()
    if not key:
        raise ValueError(
            "Groq API key not found. Add GROQ_API_KEY (preferred) or GROQ_KEY "
            "to .streamlit/secrets.toml or your environment."
        )
    return Groq(api_key=key)


def _get_groq_api_key():
    secret_keys = ("GROQ_API_KEY", "GROQ_KEY")

    try:
        for secret_key in secret_keys:
            value = st.secrets.get(secret_key, "")
            if value:
                return value
    except Exception:
        pass

    for env_key in secret_keys:
        value = os.environ.get(env_key, "")
        if value:
            return value

    return ""


def groq_json_decision(system_prompt, user_prompt, *, model="llama-3.1-8b-instant",
                       max_tokens=900, temperature=0.1):
    """Ask Groq for a JSON decision and return a parsed dict.

    Returns None when the model is unavailable or the payload cannot be parsed.
    """
    try:
        client = get_groq_client()
        resp = client.chat.completions.create(
            model=model,
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
    """Auto-detect and compute business KPIs from a cleaned dataframe.

    Returns a list of dicts: {label, value, sub, color_class}
    Always returns at least 4 KPIs.
    """
    import numpy as np

    numeric = [c for c in df.select_dtypes(include=[np.number]).columns
               if not is_identifier_col(c)]

    kpis = []

    # Revenue / main sales metric
    revenue_col = choose_main_numeric(numeric)
    if revenue_col:
        total = df[revenue_col].sum()
        avg   = df[revenue_col].mean()
        kpis.append({
            "label": revenue_col.replace("_", " ").title(),
            "value": _fmt_number(total),
            "sub":   f"avg {_fmt_number(avg)} per record",
            "color": "kpi-blue",
            "icon":  "💰",
        })

    # Profit & margin
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
        kpis.append({
            "label": profit_col.replace("_", " ").title(),
            "value": _fmt_number(df[profit_col].sum()),
            "sub":   f"avg {_fmt_number(df[profit_col].mean())} per record",
            "color": "kpi-green",
            "icon":  "📈",
        })

    # Record count
    kpis.append({
        "label": "Total Records",
        "value": f"{len(df):,}",
        "sub":   f"{df.shape[1]} columns",
        "color": "kpi-purple",
        "icon":  "📋",
    })

    # Quantity / volume
    qty_col = next((c for c in numeric
                    if "qty" in c.lower() or "quantity" in c.lower()
                    or "units" in c.lower() or "count" in c.lower()), None)
    if qty_col:
        kpis.append({
            "label": qty_col.replace("_", " ").title(),
            "value": f"{int(df[qty_col].sum()):,}",
            "sub":   f"avg {df[qty_col].mean():.1f} per order",
            "color": "kpi-amber",
            "icon":  "📦",
        })

    # Discount / rate metric
    disc_col = next((c for c in numeric
                     if "discount" in c.lower() or "rate" in c.lower()
                     or "pct" in c.lower() or "percent" in c.lower()), None)
    if disc_col and len(kpis) < 6:
        kpis.append({
            "label": disc_col.replace("_", " ").title(),
            "value": f"{df[disc_col].mean():.1f}%",
            "sub":   f"avg across {len(df):,} records",
            "color": "kpi-rose",
            "icon":  "🏷️",
        })

    # Fallback: add more numeric KPIs if we have fewer than 4
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

    return kpis[:6]  # max 6 KPIs


def _fmt_number(n):
    """Format a number compactly: 1.2M, 45.3K, 123."""
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
    """Return an HTML badge for a column's type."""
    name = col_name.lower()
    if is_identifier_col(col_name):
        return '<span style="background:#F1F5F9;color:#64748B;padding:2px 8px;border-radius:10px;font-size:0.72rem;font-weight:600;">ID</span>'
    if "date" in name or "time" in name:
        return '<span style="background:#FEF3C7;color:#D97706;padding:2px 8px;border-radius:10px;font-size:0.72rem;font-weight:600;">📅 DATE</span>'
    if "int" in dtype_str or "float" in dtype_str:
        return '<span style="background:#DBEAFE;color:#1D4ED8;padding:2px 8px;border-radius:10px;font-size:0.72rem;font-weight:600;">🔢 NUM</span>'
    return '<span style="background:#F0FDF4;color:#16A34A;padding:2px 8px;border-radius:10px;font-size:0.72rem;font-weight:600;">🔤 TEXT</span>'


# ── Markdown → safe HTML ──────────────────────────────────────────────────────

def md_to_html(text):
    """Convert a subset of markdown to HTML for use inside st.markdown divs.

    Handles: ## headings, **bold**, *italic*, bullet lists, line breaks.
    Does NOT use a full markdown parser to avoid extra dependencies.
    """
    if not text:
        return ""

    lines = text.split("\n")
    out = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Headings
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

        # Bullet lists
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                out.append('<ul style="margin:0.4rem 0 0.4rem 1.2rem;padding:0;">')
                in_list = True
            item = stripped[2:]
            item = _inline_md(item)
            out.append(f'<li style="margin-bottom:4px;color:#374151;">{item}</li>')
            continue

        # Close list if needed
        if in_list and stripped:
            out.append("</ul>")
            in_list = False

        # Empty line → paragraph break
        if not stripped:
            out.append('<div style="height:6px;"></div>')
            continue

        # Regular paragraph
        out.append(f'<p style="margin:0 0 6px 0;color:#374151;line-height:1.65;">{_inline_md(stripped)}</p>')

    if in_list:
        out.append("</ul>")

    return "\n".join(out)


def _inline_md(text):
    """Convert inline **bold**, *italic*, and `code` to HTML."""
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Italic (single asterisk, not double)
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.+?)`', r'<code style="background:#F1F5F9;padding:1px 5px;border-radius:3px;font-size:0.88em;">\1</code>', text)
    return text


# ── Suggested Q&A questions ───────────────────────────────────────────────────

def suggest_questions(df):
    """Generate 4 relevant Q&A suggestions based on detected columns."""
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

    # Deduplicate and return first 4
    seen = set()
    unique = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique[:4]


# ── Data-summary builder ──────────────────────────────────────────────────────

def build_data_context(df, understanding=""):
    """Build a rich, LLM-friendly text summary of a dataframe."""
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
