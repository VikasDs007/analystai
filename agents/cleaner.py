"""Cleaner agent — fixes data quality issues detected by the detective."""

import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.helpers import llm_json_decision


def run_cleaner(df, issues, use_llm=True):
    """Apply fixes for each detected issue.

    Returns (cleaned_df, report_lines).
    """
    df_clean = df.copy()
    report = []
    seen = set()  # prevent double-processing same issue type

    cleaning_plan = llm_json_decision(
        """
You are a cautious data-cleaning planner.
Return only valid JSON with these keys:
{
  "recommended_cleaning_order": ["issue types to fix first"],
  "priority_columns": ["columns to pay special attention to"],
  "skip_issue_types": ["issue types to skip if low confidence"],
  "confidence": 0.0,
  "reason": "short reason for the plan"
}

The plan must be conservative and based only on the provided issues.
""".strip(),
        f"Issues detected: {issues}\n\nSample rows:\n{df.head(5).to_string()}",
        max_tokens=500,
        temperature=0.1,
    )

    issue_priority = {}
    if isinstance(cleaning_plan, dict):
        for idx, issue_type in enumerate(cleaning_plan.get("recommended_cleaning_order", [])):
            issue_priority[issue_type] = idx

    issues_to_process = list(issues)
    if issue_priority:
        issues_to_process.sort(key=lambda issue: issue_priority.get(issue.get("type", ""), 999))

    for issue in issues_to_process:
        itype = issue["type"]
        col = issue.get("column", "")

        # ── Duplicates ────────────────────────────────────────────────────────
        if itype == "duplicate_rows" and "duplicates" not in seen:
            before = len(df_clean)
            df_clean = df_clean.drop_duplicates().reset_index(drop=True)
            removed = before - len(df_clean)
            if removed > 0:
                report.append(f"✅ Removed {removed} duplicate rows")
            seen.add("duplicates")

        # ── Missing values ────────────────────────────────────────────────────
        elif itype == "missing_values" and col in df_clean.columns:
            count = int(df_clean[col].isnull().sum())
            if count > 0:
                if pd.api.types.is_numeric_dtype(df_clean[col]):
                    fill_val = df_clean[col].median()
                    df_clean[col] = df_clean[col].fillna(fill_val)
                    report.append(
                        f"✅ Filled {count} missing values in "
                        f"'{col}' with median ({fill_val:,.1f})"
                    )
                else:
                    mode_vals = df_clean[col].mode()
                    if len(mode_vals) > 0:
                        df_clean[col] = df_clean[col].fillna(mode_vals[0])
                        report.append(
                            f"✅ Filled {count} missing values in "
                            f"'{col}' with most common value "
                            f"('{mode_vals[0]}')"
                        )

        # ── Outliers ──────────────────────────────────────────────────────────
        elif itype == "outliers" and col in df_clean.columns:
            q1 = df_clean[col].quantile(0.25)
            q3 = df_clean[col].quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                lo, hi = q1 - 3 * iqr, q3 + 3 * iqr
                out_count = int(
                    ((df_clean[col] < lo) | (df_clean[col] > hi)).sum()
                )
                if out_count > 0:
                    df_clean[col] = df_clean[col].clip(lo, hi)
                    report.append(
                        f"✅ Capped {out_count} extreme values in '{col}' "
                        f"to [{lo:,.1f} – {hi:,.1f}]"
                    )

        # ── Inconsistent text ─────────────────────────────────────────────────
        elif itype == "inconsistent_text" and col in df_clean.columns:
            df_clean[col] = df_clean[col].str.strip().str.title()
            report.append(f"✅ Standardized text casing in '{col}'")

        # ── Date Normalization ────────────────────────────────────────────────
        elif itype == "date_normalization" and col in df_clean.columns:
            try:
                parsed = pd.to_datetime(df_clean[col], errors="coerce", format="mixed")
                if parsed.isnull().all():
                    parsed = pd.to_datetime(df_clean[col], errors="coerce")
                if parsed.notna().any():
                    non_null_parsed = parsed.dropna()
                    has_time = (non_null_parsed.dt.hour != 0).any() | (non_null_parsed.dt.minute != 0).any()
                    if has_time:
                        df_clean[col] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        df_clean[col] = parsed.dt.strftime("%Y-%m-%d")
                    # Replace Strftime 'NaT' representation back to NaN
                    df_clean[col] = df_clean[col].where(parsed.notnull(), np.nan)
                    report.append(f"✅ Normalized date formatting in '{col}' to YYYY-MM-DD standard")
            except Exception as e:
                report.append(f"⚠️ Failed to normalize dates in '{col}': {str(e)}")

        # ── Unnamed or Empty Columns ──────────────────────────────────────────
        elif itype == "unnamed_or_empty_column" and col in df_clean.columns:
            df_clean = df_clean.drop(columns=[col])
            report.append(f"✅ Dropped empty or unnamed column '{col}'")

    # ── Auto-convert currency-formatted text columns to numeric ───────────────
    # Only attempt on columns that are still object dtype after the above fixes
    for col in df_clean.select_dtypes(include=["object"]).columns:
        sample = df_clean[col].dropna().head(30)
        # Strip common currency symbols and thousands separators
        cleaned_sample = (
            sample.str.replace(",", "", regex=False)
                  .str.replace("₹", "", regex=False)
                  .str.replace("$", "", regex=False)
                  .str.replace("€", "", regex=False)
                  .str.strip()
        )
        try:
            converted = pd.to_numeric(cleaned_sample, errors="coerce")
            # Only convert if ≥ 80% of sampled values parse as numbers
            if converted.notna().mean() >= 0.8:
                df_clean[col] = pd.to_numeric(
                    df_clean[col]
                    .str.replace(",", "", regex=False)
                    .str.replace("₹", "", regex=False)
                    .str.replace("$", "", regex=False)
                    .str.replace("€", "", regex=False)
                    .str.strip(),
                    errors="coerce",
                )
                report.append(
                    f"✅ Converted '{col}' from text to numeric"
                )
        except Exception:
            pass  # column isn't text-numeric, skip silently

    if not report:
        report.append("✅ Data looks clean — no issues to fix.")

    return df_clean, report
