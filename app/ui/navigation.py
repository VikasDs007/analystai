"""Workspace tab navigation (stepper + sidebar sync)."""

import streamlit as st

from app.config import WORKSPACE_TABS, WORKSPACE_TAB_KEYS
from app.ui.layout import try_rerun


def get_workspace_tab(default="overview"):
    tab = st.session_state.get("workspace_tab") or default
    if tab not in WORKSPACE_TAB_KEYS:
        tab = default
    st.session_state.workspace_tab = tab
    return tab


def set_workspace_tab(tab_key):
    if tab_key in WORKSPACE_TAB_KEYS:
        st.session_state.workspace_tab = tab_key


def render_workspace_stepper():
    """Horizontal sticky stepper; sets workspace_tab on selection."""
    active = get_workspace_tab()
    st.markdown('<div class="workspace-stepper-wrap">', unsafe_allow_html=True)
    cols = st.columns(len(WORKSPACE_TABS))
    for col, (key, label) in zip(cols, WORKSPACE_TABS):
        with col:
            btn_type = "primary" if active == key else "secondary"
            if st.button(
                label,
                key=f"stepper_{key}",
                width="stretch",
                type=btn_type,
            ):
                set_workspace_tab(key)
                try_rerun()
    st.markdown("</div>", unsafe_allow_html=True)
