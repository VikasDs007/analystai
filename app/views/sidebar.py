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

        # AI status chip — always OpenAI, no mode toggle
        ai_err = st.session_state.get("groq_error")
        if ai_err:
            st.markdown(
                f'<div style="margin:6px 0 8px 0;color:#FCA5A5;font-weight:600;">🔴 AI error: {ai_err}</div>',
                unsafe_allow_html=True,
            )
        elif has_api_key():
            st.markdown(
                '<div style="margin:6px 0 8px 0;color:#BBF7D0;font-weight:600;">🟢 Powered by OpenAI</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="margin:6px 0 8px 0;color:#FDE68A;font-weight:600;">🟠 No API key found — add OPEN_ROUTER_KEY to secrets.toml</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Workspace navigation removed from the sidebar. Always show pipeline hints.
        st.markdown(
            '<p class="sb-section-label">PIPELINE</p>',
            unsafe_allow_html=True,
        )
        for key, label in WORKSPACE_TABS:
            st.caption(f"· {label}")

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

        # Short privacy hint with link to local policy document
        st.markdown(
            '<div style="font-size:0.78rem;color:#94A3B8;margin-top:8px;">Data is processed via your configured AI provider; do not upload confidential fields. <a href="/docs/PRIVACY.md">Privacy policy</a></div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Restart", use_container_width=True):
                keys = [
                    "df_raw", "df_clean", "detective_result", "charts", "insights",
                    "report", "qa_history", "last_file_name", "filters",
                    "cached_chart_specs", "workspace_tab",
                    "cleaning_decision", "cleaning_diff", "filters_dirty",
                ]
                for k in keys:
                    if k in st.session_state:
                        del st.session_state[k]
                try_rerun()
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
                use_container_width=True,
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
