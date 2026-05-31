"""Detective agent — profiles the dataframe and detects quality issues."""

import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import get_llm_client, llm_json_decision


# ── Profiling ─────────────────────────────────────────────────────────────────

def profile_dataframe(df):
    profile = {
        "rows": len(df),
        "columns": len(df.columns),
        "total_cells": df.size,
        "missing_cells": int(df.isnull().sum().sum()),
        "missing_pct": round(df.isnull().mean().mean() * 100, 1),
        "duplicate_rows": int(df.duplicated().sum()),
        "column_details": {},
    }

    for col in df.columns:
        s = df[col]
        details = {
            "dtype": str(s.dtype),
            "missing": int(s.isnull().sum()),
            "missing_pct": round(s.isnull().mean() * 100, 1),
            "unique": int(s.nunique()),
            "sample": s.dropna().head(3).tolist(),
        }
        if pd.api.types.is_numeric_dtype(s):
            details.update({
                "min": round(float(s.min()), 2),
                "max": round(float(s.max()), 2),
                "mean": round(float(s.mean()), 2),
                "std": round(float(s.std()), 2),
            })
        profile["column_details"][col] = details

    return profile


# ── Issue detection ───────────────────────────────────────────────────────────

def detect_issues(df):
    issues = []

    # Missing values
    for col in df.columns:
        missing = int(df[col].isnull().sum())
        if missing > 0:
            pct = round(missing / len(df) * 100, 1)
            issues.append({
                "type": "missing_values",
                "column": col,
                "count": missing,
                "pct": pct,
                "severity": "🔴 High" if pct > 10 else "🟡 Medium",
                "fix": "Fill with median (numbers) or mode (text)",
            })

    # Duplicate rows
    dups = int(df.duplicated().sum())
    if dups > 0:
        issues.append({
            "type": "duplicate_rows",
            "column": "entire row",
            "count": dups,
            "pct": round(dups / len(df) * 100, 1),
            "severity": "🟡 Medium",
            "fix": "Remove duplicates",
        })

    # Outliers (3×IQR rule)
    for col in df.select_dtypes(include=[np.number]).columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            mask = (df[col] < q1 - 3 * iqr) | (df[col] > q3 + 3 * iqr)
            out = int(mask.sum())
            if out > 0:
                issues.append({
                    "type": "outliers",
                    "column": col,
                    "count": out,
                    "pct": round(out / len(df) * 100, 1),
                    "severity": "🟡 Medium",
                    "fix": "Cap extreme values",
                })

    # Inconsistent text casing
    for col in df.select_dtypes(include=["object"]).columns:
        vals = df[col].dropna()
        if len(vals) > 0:
            orig = vals.nunique()
            norm = vals.str.lower().str.strip().nunique()
            if orig > norm:
                issues.append({
                    "type": "inconsistent_text",
                    "column": col,
                    "count": int(orig - norm),
                    "pct": 0,
                    "severity": "🟢 Low",
                    "fix": "Standardize casing / whitespace",
                })

    return issues


# ── Main entry point ──────────────────────────────────────────────────────────

def _quick_understanding(profile):
    return (
        f"This dataset has {profile['rows']:,} rows and {profile['columns']} columns "
        f"with about {profile['missing_pct']}% missing values and "
        f"{profile['duplicate_rows']} duplicate rows. "
        "Use Full analysis mode for a richer AI-written summary."
    )


def run_detective(df, use_llm=True):
    profile = profile_dataframe(df)
    issues = detect_issues(df)

    # Build a concise column summary for the LLM
    col_lines = []
    for col, info in profile["column_details"].items():
        line = (
            f"- {col} ({info['dtype']}): "
            f"{info['missing']} missing, "
            f"{info['unique']} unique, "
            f"sample={info['sample'][:2]}"
        )
        if "mean" in info:
            line += f", mean={info['mean']}"
        col_lines.append(line)

    context = (
        f"Dataset: {profile['rows']} rows, {profile['columns']} columns\n"
        f"Missing: {profile['missing_pct']}% of cells\n"
        f"Duplicates: {profile['duplicate_rows']} rows\n\n"
        f"Columns:\n" + "\n".join(col_lines) +
        f"\n\nFirst 3 rows:\n{df.head(3).to_string()}"
    )

    try:
        client = get_llm_client()
        resp = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly data analyst talking to a small "
                        "business owner. Look at their data and explain in "
                        "3-4 simple sentences:\n"
                        "1. What this data is about\n"
                        "2. What kind of business this likely is\n"
                        "3. One interesting thing you notice\n\n"
                        "Use simple words. Be warm and encouraging. "
                        "No technical terms. Max 80 words."
                    ),
                },
                {"role": "user", "content": context},
            ],
            max_tokens=150,
            temperature=0.4,
        )
        understanding = resp.choices[0].message.content.strip()
    except Exception as exc:
        understanding = (
            f"This dataset has {profile['rows']} records across "
            f"{profile['columns']} columns. "
            "It looks like business or sales data."
            f" (Note: AI description unavailable — {exc})"
        )

    decision_summary = llm_json_decision(
        """
You are a cautious data-quality reviewer.
Return only valid JSON with these keys:
{
  "business_summary": "One clear sentence about what the data appears to represent.",
  "risk_level": "low|medium|high",
  "high_priority_issues": ["short issue labels ordered by priority"],
  "recommended_cleaning_order": ["steps to fix first"],
  "qa_guardrails": ["rules that later Q&A should follow"],
  "confidence": 0.0
}

Keep the result grounded in the supplied data only. No markdown.
""".strip(),
        """
Use the following data snapshot to make a conservative decision.

UNDERSTANDING:
{understanding}

PROFILE:
rows={rows}, columns={columns}, missing_pct={missing_pct}, duplicate_rows={duplicate_rows}

ISSUES:
{issues}

SAMPLE ROWS:
{sample_rows}
""".strip().format(
            understanding=understanding,
            rows=profile["rows"],
            columns=profile["columns"],
            missing_pct=profile["missing_pct"],
            duplicate_rows=profile["duplicate_rows"],
            issues=issues[:8],
            sample_rows=df.head(5).to_string(),
        ),
        max_tokens=700,
        temperature=0.1,
    )

    if isinstance(decision_summary, dict):
        understanding = decision_summary.get("business_summary", understanding) or understanding

    return {
        "understanding": understanding,
        "profile": profile,
        "issues": issues,
        "decision_summary": decision_summary,
    }
