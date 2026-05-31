"""Pipeline progress and export helpers."""

import json
import re

import streamlit as st

def current_pipeline_step():
    """Return the current pipeline step index (0..5) for the sidebar.

    Steps: 0=Detective, 1=Cleaner, 2=Charts, 3=Insights, 4=Report, 5=Q&A
    The function inspects `st.session_state` keys to determine progress.
    """
    # If no detective output yet, we are at Detect
    if st.session_state.get("detective_result") is None:
        return 0
    # If cleaned data not present, show Cleaner
    if st.session_state.get("df_clean") is None:
        return 1
    # If there are no generated charts or cached specs, show Charts
    charts = st.session_state.get("charts")
    cached = st.session_state.get("cached_chart_specs")
    if (not charts) and (not cached):
        return 2
    # If insights not generated, show Insights
    if st.session_state.get("insights") is None:
        return 3
    # If report not generated, show Report
    if st.session_state.get("report") is None:
        return 4
    # Otherwise show Q&A
    return 5


def count_imputed_values(cleaning_report):
    """Estimate the number of imputed/missing values from the cleaning_report.

    The cleaning_report is expected to be a list of human-readable step strings.
    We look for integer counts followed by keywords like 'imput' or 'missing'.
    """
    import re
    if not cleaning_report:
        return 0
    total = 0
    for item in cleaning_report:
        try:
            if not isinstance(item, str):
                continue
            m = re.search(r"(\d{1,9})\s*(?:missing|imput|imputed|filled)", item, re.IGNORECASE)
            if m:
                total += int(m.group(1))
        except Exception:
            continue
    return total


def build_dataset_snapshot(df, df_clean):
    """Build a simple list of snapshot items for the top hero stat cards."""
    cleaned = df_clean if df_clean is not None else df
    try:
        missing = int(df.isnull().sum().sum())
    except Exception:
        missing = 0
    items = [
        {"label": "File", "value": st.session_state.get("last_file_name") or st.session_state.get("last_file_id", "dataset"), "sub": "active source", "color": "primary"},
        {"label": "Rows", "value": f"{len(df):,}", "sub": f"{len(df.columns)} columns", "color": "primary"},
        {"label": "Cleaned Rows", "value": f"{len(cleaned):,}", "sub": "after cleaning" if df_clean is not None else "pending", "color": ""},
        {"label": "Missing", "value": f"{missing:,}", "sub": "total nulls", "color": ""},
    ]
    return items


def create_download_pack_bytes():
    """Create an in-memory zip containing report, cleaned CSV, and chart specs.

    Returns bytes suitable for `st.download_button`.
    """
    import io
    import zipfile

    bio = io.BytesIO()
    try:
        with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as z:
            # analysis report
            report = st.session_state.get("report") or ""
            z.writestr("analysis_report.md", report)

            # cleaned data
            df_clean = st.session_state.get("df_clean")
            if df_clean is not None:
                try:
                    csv_bytes = df_clean.to_csv(index=False).encode("utf-8")
                    z.writestr("cleaned_data.csv", csv_bytes)
                except Exception:
                    # skip if conversion fails
                    pass

            # chart specs / cached specs
            specs = st.session_state.get("cached_chart_specs") or st.session_state.get("charts") or []
            try:
                z.writestr("chart_specs.json", json.dumps(specs, ensure_ascii=False, indent=2))
            except Exception:
                pass
    except Exception:
        return b""
    bio.seek(0)
    return bio.read()
