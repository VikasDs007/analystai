"""Persist and restore pipeline outputs on disk."""

import json
import os

import pandas as pd
import streamlit as st

from app.config import CACHE_CLEAN_CSV, CACHE_STATE

def load_cached_pipeline_state():
    """Restore pipeline outputs from disk if available."""
    if not os.path.exists(CACHE_STATE):
        return
    try:
        with open(CACHE_STATE, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        if payload.get("detective_result"):
            st.session_state.detective_result = payload["detective_result"]
        if payload.get("cleaning_report"):
            st.session_state.cleaning_report = payload["cleaning_report"]
        if payload.get("anomalies") is not None:
            st.session_state.anomalies = payload["anomalies"]
        if payload.get("chart_specs"):
            st.session_state.cached_chart_specs = payload["chart_specs"]
        if payload.get("insights"):
            st.session_state.insights = payload["insights"]
        if payload.get("report"):
            st.session_state.report = payload["report"]
        if payload.get("last_file_id"):
            st.session_state.last_file_id = payload["last_file_id"]
        if payload.get("last_file_name"):
            st.session_state.last_file_name = payload["last_file_name"]
        if payload.get("tour_completed"):
            st.session_state.tour_completed = payload["tour_completed"]
        if payload.get("workspace_tab"):
            st.session_state.workspace_tab = payload["workspace_tab"]
        if payload.get("qa_history"):
            st.session_state.qa_history = payload["qa_history"]
        if payload.get("filters"):
            st.session_state.filters = payload["filters"]
        if os.path.exists(CACHE_CLEAN_CSV):
            st.session_state.df_clean = pd.read_csv(CACHE_CLEAN_CSV)
            if not st.session_state.get("cleaning_decision"):
                st.session_state.cleaning_decision = "auto"
    except Exception:
        pass


def save_cached_pipeline_state():
    """Persist all pipeline outputs so refreshes restore the full session."""
    payload = {
        "detective_result": st.session_state.get("detective_result"),
        "cleaning_report": st.session_state.get("cleaning_report"),
        "anomalies": st.session_state.get("anomalies"),
        "chart_specs": st.session_state.get("cached_chart_specs"),
        "insights": st.session_state.get("insights"),
        "report": st.session_state.get("report"),
        "last_file_id": st.session_state.get("last_file_id"),
        "last_file_name": st.session_state.get("last_file_name"),
        "tour_completed": st.session_state.get("tour_completed"),
        "workspace_tab": st.session_state.get("workspace_tab"),
        "qa_history": st.session_state.get("qa_history") or [],
        "filters": st.session_state.get("filters") or {},
    }
    try:
        with open(CACHE_STATE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass


def clear_cached_pipeline_state():
    """Remove persisted generated outputs."""
    for path in [CACHE_STATE, CACHE_CLEAN_CSV]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
