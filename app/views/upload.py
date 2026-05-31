"""CSV upload, sample data, and dataset resolution."""

import os
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from app.config import CACHE_CSV, SAMPLE_CSV, UPLOAD_CLEAR_KEYS
from app.state.cache import (
    clear_cached_pipeline_state,
    save_cached_pipeline_state,
)
from app.ui.layout import try_rerun

# Upload limits
MAX_FILE_BYTES = 10_000_000  # 10 MB
MAX_ROWS = 200_000
PREVIEW_ROWS = 100


def _handle_file_preview(uploaded_file):
    """Show preview + confirm buttons for a newly uploaded file.

    Returns True if the file has been confirmed and is ready to process,
    False if we should stop and wait for user action.
    """
    try:
        fsize = getattr(uploaded_file, "size", None)
    except Exception:
        fsize = None
    if fsize and fsize > MAX_FILE_BYTES:
        st.error(f"File too large ({fsize/1e6:.1f} MB). Max is {MAX_FILE_BYTES/1e6:.0f} MB.")
        return False

    prev_name = st.session_state.get("uploaded_file_name")
    already_confirmed = (
        st.session_state.get("upload_confirmed")
        and prev_name == getattr(uploaded_file, "name", None)
    )
    if already_confirmed:
        return True

    # Read preview
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    preview_df = None
    used_encoding = "utf-8"
    try:
        preview_df = pd.read_csv(uploaded_file, nrows=PREVIEW_ROWS, encoding="utf-8")
    except Exception:
        try:
            uploaded_file.seek(0)
            preview_df = pd.read_csv(uploaded_file, nrows=PREVIEW_ROWS, encoding="latin-1")
            used_encoding = "latin-1"
        except Exception as e:
            st.error(f"Could not read file preview: {e}")
            return False

    st.markdown(f"**Preview — first {PREVIEW_ROWS} rows**")
    st.dataframe(preview_df, use_container_width=True, height=220)
    st.caption(f"Encoding: {used_encoding} · {len(preview_df):,} rows shown")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("✅ Process full file", type="primary", use_container_width=True, key="btn_process_full"):
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
            st.session_state["uploaded_file_bytes"] = uploaded_file.getvalue()
            st.session_state["upload_confirmed"] = True
            st.session_state["uploaded_file_name"] = getattr(uploaded_file, "name", None)
    with c2:
        # Let user pick how many rows to trim to
        trim_n = st.number_input(
            "Trim to N rows",
            min_value=100,
            max_value=MAX_ROWS,
            value=min(10_000, MAX_ROWS),
            step=1000,
            key="trim_row_count",
            label_visibility="collapsed",
        )
        if st.button(f"✂️ Trim to {int(trim_n):,} rows", use_container_width=True, key="btn_trim"):
            try:
                uploaded_file.seek(0)
            except Exception:
                pass
            st.session_state["uploaded_file_bytes"] = uploaded_file.getvalue()
            st.session_state["upload_confirmed"] = True
            st.session_state["upload_trim"] = True
            st.session_state["upload_trim_n"] = int(trim_n)
            st.session_state["uploaded_file_name"] = getattr(uploaded_file, "name", None)
    with c3:
        if st.button("✖ Cancel", use_container_width=True, key="btn_cancel"):
            if "csv_uploader" in st.session_state:
                del st.session_state["csv_uploader"]
            st.session_state["upload_confirmed"] = False
            try_rerun()

    return bool(st.session_state.get("upload_confirmed"))


def render_landing_upload_zone():
    """Styled upload zone + prominent sample data CTA for the landing page."""

    # ── Styled upload zone visual header ─────────────────────────────────────
    components.html(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
          * { box-sizing: border-box; font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
          .upload-zone {
            border: 2px dashed #6366F1;
            border-radius: 16px;
            background: linear-gradient(135deg, #F8F7FF 0%, #EEF2FF 100%);
            padding: 28px 32px 20px;
            text-align: center;
            margin-bottom: 4px;
          }
          .upload-icon { font-size: 2.4rem; margin-bottom: 10px; }
          .upload-title { font-size: 1.05rem; font-weight: 700; color: #1E293B; margin-bottom: 6px; }
          .upload-sub   { font-size: 0.82rem; color: #64748B; margin-bottom: 14px; line-height: 1.5; }
          .upload-hint  {
            display: inline-block;
            background: #EEF2FF; border: 1px solid #C7D2FE;
            color: #4338CA; border-radius: 999px;
            padding: 4px 14px; font-size: 0.75rem; font-weight: 600;
          }
        </style>
        <div class="upload-zone">
          <div class="upload-icon">☁️</div>
          <div class="upload-title">Drag &amp; drop your CSV file here</div>
          <div class="upload-sub">
            Supports any CSV up to 10 MB · Sales, inventory, surveys, finance — anything works
          </div>
          <span class="upload-hint">↓ Use the file picker below ↓</span>
        </div>
        """,
        height=190,
        scrolling=False,
    )

    # ── Uploader styling ──────────────────────────────────────────────────────
    st.markdown(
        """
        <style>
        [data-testid="stFileUploader"] {
            border: 1px solid #C7D2FE !important;
            border-top: none !important;
            border-radius: 0 0 16px 16px !important;
            background: #FAFBFF !important;
            padding: 0 !important;
        }
        [data-testid="stFileUploader"] section { border: none !important; padding: 12px 20px !important; }
        [data-testid="stFileUploader"] label { display: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"],
        label_visibility="collapsed",
        help="Upload any CSV file up to 10 MB",
        key="csv_uploader",
    )
    st.markdown('<div id="tour-upload" style="height:0px;width:0px;"></div>', unsafe_allow_html=True)

    # ── Preview + confirm buttons (same logic as workspace uploader) ──────────
    if uploaded_file is not None:
        _handle_file_preview(uploaded_file)

    # ── Sample data CTA ───────────────────────────────────────────────────────
    st.markdown(
        '<div style="display:flex;align-items:center;gap:10px;margin:16px 0 4px 0;">'
        '<div style="flex:1;height:1px;background:#E2E8F0;"></div>'
        '<span style="font-size:0.78rem;color:#94A3B8;font-weight:500;white-space:nowrap;">'
        'or try with sample data'
        '</span>'
        '<div style="flex:1;height:1px;background:#E2E8F0;"></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_sample, col_spacer = st.columns([2, 3])
    with col_sample:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#0F172A,#1E3A5F);'
            'border:1px solid #334155;border-radius:14px;padding:14px 18px;margin-bottom:4px;">'
            '<div style="display:flex;align-items:center;gap:10px;">'
            '<span style="font-size:1.5rem;">📦</span>'
            '<div>'
            '<div style="font-weight:700;color:#F1F5F9;font-size:0.9rem;">Sample Sales Dataset</div>'
            '<div style="color:#94A3B8;font-size:0.78rem;margin-top:2px;">120 rows · 14 columns · retail sales data</div>'
            '</div></div></div>',
            unsafe_allow_html=True,
        )
        if st.button("▶ Load sample data", use_container_width=True, type="primary", key="sample_btn_landing"):
            _load_sample_data()

    return uploaded_file


def render_upload_controls():
    """Compact uploader for the workspace view (data already loaded). Returns uploaded file."""
    up_col, btn_col = st.columns([4, 1])

    with up_col:
        uploaded_file = st.file_uploader(
            "CSV",
            type=["csv"],
            label_visibility="collapsed",
            help="Upload any CSV file",
            key="csv_uploader",
        )
        st.markdown('<div id="tour-upload" style="height:0px;width:0px;"></div>', unsafe_allow_html=True)

        if uploaded_file is not None:
            confirmed = _handle_file_preview(uploaded_file)
            if not confirmed:
                return uploaded_file

        # ── File already loaded — show name + remove button ───────────────────
        if st.session_state.get("df_raw") is not None and uploaded_file is None:
            file_name = st.session_state.get("last_file_name") or "(in-memory)"
            st.markdown(
                f'<div style="color:#0F172A;font-weight:600;margin:6px 0 8px 0;">'
                f'📄 Loaded: {file_name}</div>',
                unsafe_allow_html=True,
            )
            if st.button("Remove File"):
                for k in UPLOAD_CLEAR_KEYS:
                    if k in st.session_state:
                        del st.session_state[k]
                if "csv_uploader" in st.session_state:
                    del st.session_state["csv_uploader"]
                st.session_state.skip_cache_reload = True
                st.session_state.cleaning_decision = None
                st.session_state.cleaning_diff = None
                st.session_state.filters_dirty = False
                clear_cached_pipeline_state()
                try_rerun()

    with btn_col:
        if st.button("Sample data", key="sample_btn_workspace"):
            _load_sample_data()

    return uploaded_file


def _load_sample_data():
    """Load the sample CSV into session state and navigate to workspace."""
    try:
        df_sample = pd.read_csv(SAMPLE_CSV)
        st.session_state.df_raw = df_sample
        st.session_state.last_file_id = "sample"
        st.session_state.last_file_name = "sample_sales.csv"
        st.session_state.workspace_tab = "overview"
        st.session_state.cleaning_decision = None
        st.session_state.cleaning_diff = None
        st.session_state.filters_dirty = False
        st.session_state.skip_cache_reload = False
        save_cached_pipeline_state()
        try_rerun()
    except Exception as e:
        st.error(f"Failed to load sample data: {e}")


def resolve_dataset(uploaded_file):
    """Parse the confirmed upload or return df_raw from session. Never blocks."""
    df = None

    if st.session_state.get("upload_confirmed"):
        data_bytes = st.session_state.get("uploaded_file_bytes")

        if not data_bytes and uploaded_file is not None:
            try:
                uploaded_file.seek(0)
                data_bytes = uploaded_file.getvalue()
            except Exception:
                data_bytes = None

        if not data_bytes:
            st.error("Upload data not available — please re-upload.")
            st.session_state["upload_confirmed"] = False
            return None

        try:
            bio = BytesIO(data_bytes)
            try:
                df = pd.read_csv(bio, encoding="utf-8")
            except Exception:
                bio.seek(0)
                df = pd.read_csv(bio, encoding="latin-1")

            if len(df) > MAX_ROWS:
                if st.session_state.get("upload_trim"):
                    trim_n = st.session_state.get("upload_trim_n") or MAX_ROWS
                    df = df.head(trim_n)
                else:
                    st.warning(f"File has {len(df):,} rows — trimmed to {MAX_ROWS:,}.")
                    df = df.head(MAX_ROWS)

            st.session_state.df_raw = df
            st.session_state.last_file_name = st.session_state.get("uploaded_file_name", "uploaded.csv")
            st.session_state.last_file_id = "uploaded"
            st.session_state.workspace_tab = "overview"
            st.session_state.cleaning_decision = None
            st.session_state.cleaning_diff = None
            st.session_state.filters_dirty = False

            st.session_state["upload_confirmed"] = False
            st.session_state["uploaded_file_bytes"] = None
            st.session_state["upload_trim"] = False
            st.session_state["upload_trim_n"] = None

            try:
                df.to_csv(CACHE_CSV, index=False)
            except Exception:
                pass
            save_cached_pipeline_state()

        except Exception as e:
            st.error(f"Failed to read CSV: {e}")
            st.session_state["upload_confirmed"] = False
            return None

    elif st.session_state.get("df_raw") is not None:
        df = st.session_state.df_raw

    return df
