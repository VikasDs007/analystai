"""Streamlit session state initialization."""

import os
import pandas as pd
import streamlit as st


def init_session_state():
    from app.config import SESSION_KEYS, CACHE_CSV, CACHE_STATE, CACHE_CLEAN_CSV
    from app.state.cache import load_cached_pipeline_state

    for key in SESSION_KEYS:
        if key not in st.session_state:
            st.session_state[key] = None
    if not st.session_state.qa_history:
        st.session_state.qa_history = []
    if not st.session_state.filters:
        st.session_state.filters = {}
    if not st.session_state.get("workspace_tab"):
        st.session_state.workspace_tab = "overview"
    if st.session_state.filters_dirty is None:
        st.session_state.filters_dirty = False
    if st.session_state.get("clear_qa_question_input"):
        st.session_state.qa_question_input = ""
        st.session_state.clear_qa_question_input = None

    # ── Restore previous session on refresh ──────────────────────────────────
    # Only restore if:
    #   1. df_raw is not already in session (fresh page load / refresh)
    #   2. A cached CSV exists on disk
    #   3. The last session was a real upload (not sample data) — we don't
    #      auto-restore sample data so the landing page stays clean
    if (
        st.session_state.get("df_raw") is None
        and not st.session_state.get("skip_cache_reload")
        and os.path.exists(CACHE_CSV)
        and os.path.exists(CACHE_STATE)
    ):
        try:
            import json
            with open(CACHE_STATE, "r", encoding="utf-8") as fh:
                meta = json.load(fh)
            last_file_id = meta.get("last_file_id", "")
            # Only auto-restore real uploads, not sample data
            if last_file_id and last_file_id not in ("sample", ""):
                df_cached = pd.read_csv(CACHE_CSV)
                st.session_state.df_raw = df_cached
                load_cached_pipeline_state()
                st.session_state.session_restored = True
        except Exception:
            pass
