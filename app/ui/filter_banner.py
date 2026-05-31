"""Banner when sidebar filters invalidate charts and report."""

import streamlit as st

from app.ui.layout import try_rerun


def render_filters_dirty_banner():
    if not st.session_state.get("filters_dirty"):
        return

    st.markdown(
        """
        <div class="filter-dirty-banner">
            <strong>Filters changed</strong> — charts and report may be out of date for the current selection.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Regenerate charts & report", type="primary", key="regen_filtered_artifacts"):
        for key in ("charts", "insights", "report", "cached_chart_specs", "anomalies"):
            st.session_state[key] = None
        st.session_state.filters_dirty = False
        try_rerun()
