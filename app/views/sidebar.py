"""Application sidebar."""

import streamlit as st

from agents.chart_selector import get_col_types
from app.config import WORKSPACE_TABS
from app.ui.layout import try_rerun
from app.ui.pipeline import create_download_pack_bytes
from utils.helpers import has_api_key


SIDEBAR_NAV = [
    ("overview", "📋", "Overview"),
    ("quality", "🚨", "Data quality"),
    ("charts", "📊", "Charts"),
    ("report", "📖", "Report"),
    ("ask", "🤖", "Ask"),
]


def render_sidebar():
    with st.sidebar:
        st.markdown('<p class="sb-logo">📊 AnalystAI</p>', unsafe_allow_html=True)
        st.markdown(
            '<p style="color:#64748B;font-size:0.78rem;margin-top:-8px;">Data Intelligence Platform</p>',
            unsafe_allow_html=True,
        )

        # AI status chip
        ai_err = st.session_state.get("groq_error")
        if ai_err:
            st.markdown(
                f'<div style="margin:8px 0; padding:6px 12px; border-radius:8px; background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); color:#F87171; font-size:0.8rem; font-weight:600;">🔴 AI error: {ai_err}</div>',
                unsafe_allow_html=True,
            )
        elif has_api_key():
            st.markdown(
                '<div style="margin:8px 0; padding:6px 12px; border-radius:8px; background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); color:#34D399; font-size:0.8rem; font-weight:600;">🟢 Powered by OpenAI</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="margin:8px 0; padding:6px 12px; border-radius:8px; background:rgba(245,158,11,0.12); border:1px solid rgba(245,158,11,0.3); color:#FBBF24; font-size:0.8rem; font-weight:600;">🟠 API Key check secrets.toml</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Workspace navigation
        st.markdown(
            '<p class="sb-section-label">PIPELINE STATUS</p>',
            unsafe_allow_html=True,
        )
        active_tab = st.session_state.get("workspace_tab", "overview")
        for key, label in WORKSPACE_TABS:
            is_active = active_tab == key
            cls = "sb-step active" if is_active else "sb-step"
            dot_color = "var(--primary)" if is_active else "rgba(255,255,255,0.15)"
            active_indicator = f'<span class="sb-num" style="background:{dot_color}; box-shadow: none;">•</span>'
            st.markdown(
                f'<div class="{cls}">{active_indicator}<span class="sb-txt" style="color:{"#FFF !important" if is_active else "#9CA3AF !important"}">{label}</span></div>',
                unsafe_allow_html=True
            )

        if st.session_state.df_clean is not None:
            st.markdown("---")
            st.markdown('<p class="sb-section-label">FILTERS</p>', unsafe_allow_html=True)
            st.markdown('<div id="tour-filters" style="height:0px;width:0px;"></div>', unsafe_allow_html=True)
            df_c = st.session_state.df_clean
            _, cat_cols, _ = get_col_types(df_c)
            new_filters = {}
            for col in cat_cols[:4]:
                opts = sorted(df_c[col].dropna().unique().tolist())
                sel = st.multiselect(
                    col.replace("_", " ").title(),
                    opts,
                    default=st.session_state.filters.get(col, []),
                    key=f"filter_{col}",
                )
                if sel:
                    new_filters[col] = sel
            if new_filters != st.session_state.filters:
                st.session_state.filters = new_filters
                st.session_state.filters_dirty = True

        st.markdown("---")
        for tip in [
            "CSV files work best",
            "Keep headers in row 1",
            "Name date cols with 'date'",
            "Remove currency symbols",
        ]:
            st.markdown(
                f'<p class="sb-tip">• {tip}</p>',
                unsafe_allow_html=True,
            )

        # Privacy hint
        st.markdown(
            '<div style="font-size:0.78rem;color:#94A3B8;margin-top:8px;">Data is processed via your configured AI provider; do not upload confidential fields.</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Dark mode toggle
        dark = st.session_state.get("dark_mode", False)
        if st.button(f"{'☀️ Light' if dark else '🌙 Dark'} mode", width="stretch", key="sidebar_dark"):
            st.session_state.dark_mode = not dark
            st.rerun()

        st.markdown("---")

        # Restart with confirmation
        if st.session_state.get("_confirm_restart"):
            st.warning("**Restart?** This will clear all data and progress.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Yes, restart", type="primary", width="stretch"):
                    keys = [
                        "df_raw", "df_clean", "detective_result", "charts", "insights",
                        "report", "qa_history", "last_file_name", "filters",
                        "cached_chart_specs", "workspace_tab",
                        "cleaning_decision", "cleaning_diff", "filters_dirty",
                        "_confirm_restart",
                    ]
                    for k in keys:
                        if k in st.session_state:
                            del st.session_state[k]
                    try_rerun()
            with c2:
                if st.button("Cancel", width="stretch"):
                    st.session_state._confirm_restart = False
                    st.rerun()
        else:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Restart", width="stretch"):
                    st.session_state._confirm_restart = True
                    st.rerun()
            with col2:
                report = st.session_state.get("report")
                df_clean_state = st.session_state.get("df_clean")
                cached_specs = st.session_state.get("cached_chart_specs")
                has_artifacts = (
                    (report is not None and report != "")
                    or (df_clean_state is not None)
                    or (cached_specs is not None)
                )
                data = create_download_pack_bytes() if has_artifacts else b""
                st.download_button(
                    "Download pack",
                    data=data,
                    file_name="analystai_pack.zip",
                    disabled=not has_artifacts,
                    width="stretch",
                )

        with st.expander("Help & onboarding", expanded=False):
            st.markdown(
                """
                - Upload a CSV or load **sample data** to start.
                - Use the workspace tabs: Overview → Quality → Charts → Report.
                - **Ask** is always available in the panel on the right.
                """
            )
            if st.button("Show onboarding"):
                st.session_state.onboarding_seen = None
            if st.button("Take tour"):
                st.session_state.show_tour = True
                st.session_state.tour_step = 0
