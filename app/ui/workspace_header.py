"""Compact workspace header (replaces large marketing hero when data is loaded)."""

import html

import streamlit as st

from app.ui.pipeline import build_dataset_snapshot
from app.ui.layout import render_stat_cards


def _pipeline_status(df, df_clean):
    if st.session_state.get("report"):
        return ("Ready", "status-ready", "Analysis complete")
    if st.session_state.get("charts"):
        return ("Charts", "status-progress", "Charts generated")
    if df_clean is not None:
        return ("Cleaned", "status-progress", "Data cleaned")
    if st.session_state.get("detective_result"):
        if st.session_state.get("cleaning_decision") == "pending":
            return ("Review", "status-progress", "Awaiting cleaning choice")
        return ("Profiling", "status-progress", "Profile complete")
    return ("Loading", "status-progress", "Processing…")


def render_compact_header(df, df_clean):
    file_name = html.escape(
        str(st.session_state.get("last_file_name") or st.session_state.get("last_file_id") or "dataset")
    )
    status_label, status_cls, status_sub = _pipeline_status(df, df_clean)
    filtered_n = len(df_clean) if df_clean is not None else len(df)

    st.markdown(
        f"""
        <div class="workspace-header">
            <div class="workspace-header-main">
                <div class="workspace-header-title">📊 AnalystAI workspace</div>
                <div class="workspace-header-meta">
                    <span class="wh-pill"><strong>File</strong> {file_name}</span>
                    <span class="wh-pill">{len(df):,} rows · {len(df.columns)} cols</span>
                    <span class="wh-pill">{filtered_n:,} cleaned rows</span>
                </div>
            </div>
            <div class="workspace-header-status {status_cls}">
                <span class="wh-status-label">{html.escape(status_label)}</span>
                <span class="wh-status-sub">{html.escape(status_sub)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(render_stat_cards(build_dataset_snapshot(df, df_clean)), unsafe_allow_html=True)
