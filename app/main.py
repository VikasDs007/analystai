"""AnalystAI — Streamlit entrypoint."""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import setup_path

setup_path()

from app.state.session import init_session_state
from app.styles import inject_styles
from app.views.hero import render_hero
from app.views.onboarding import render_onboarding
from app.views.sidebar import render_sidebar
from app.views.upload import render_landing_upload_zone, render_upload_controls, resolve_dataset
from app.views.welcome import render_welcome
from app.views.workspace import render_workspace

st.set_page_config(
    page_title="AnalystAI — Data Intelligence Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()
init_session_state()
render_sidebar()
render_onboarding()

# ── Dark mode class injection ─────────────────────────────────────────────────
if st.session_state.get("dark_mode"):
    st.markdown(
        '<img src="" onerror="document.body.classList.add(\'dark-mode\')" style="display:none;">',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<img src="" onerror="document.body.classList.remove(\'dark-mode\')" style="display:none;">',
        unsafe_allow_html=True,
    )

# ── Top app header — always visible ──────────────────────────────────────────
st.markdown(
    '<div style="display:flex;align-items:center;justify-content:space-between;'
    'padding:0.6rem 0 0.8rem 0;border-bottom:1px solid var(--border);margin-bottom:1rem;">'
    '<div style="display:flex;align-items:center;gap:10px;">'
    '<span style="font-size:1.6rem;">📊</span>'
    '<div>'
    '<span style="font-size:1.45rem;font-weight:800;color:var(--text-primary);letter-spacing:-0.5px;">AnalystAI</span>'
    '<span style="font-size:0.78rem;color:var(--text-muted);margin-left:10px;font-weight:500;">Data Intelligence Platform</span>'
    '</div></div>'
    '<div style="font-size:0.72rem;color:var(--text-faint);font-weight:500;background:var(--bg-muted);'
    'border:1px solid var(--border);border-radius:999px;padding:4px 12px;">⚡ Created by OpenAI Codex</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ── Session restored banner ───────────────────────────────────────────────────
if st.session_state.get("session_restored"):
    col_msg, col_btn = st.columns([5, 1])
    with col_msg:
        fname = st.session_state.get("last_file_name", "your last file")
        st.success(f"Session restored — continuing with **{fname}**. All your progress is back.")
    with col_btn:
        if st.button("Start fresh", key="start_fresh_banner"):
            from app.state.cache import clear_cached_pipeline_state
            from app.config import UPLOAD_CLEAR_KEYS
            clear_cached_pipeline_state()
            for k in UPLOAD_CLEAR_KEYS:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state.session_restored = False
            st.session_state.df_raw = None
            from app.ui.layout import try_rerun
            try_rerun()
    st.session_state.session_restored = False  # only show once per load

has_data = st.session_state.get("df_raw") is not None

if not has_data:
    render_hero()
    uploaded_file = render_landing_upload_zone()
else:
    uploaded_file = render_upload_controls()

df = resolve_dataset(uploaded_file)

# ── Confetti on first analysis complete ───────────────────────────────────────
if (
    st.session_state.get("detective_result") is not None
    and not st.session_state.get("confetti_shown")
    and has_data
):
    from app.ui.components import render_confetti
    render_confetti()
    st.session_state.confetti_shown = True

# ── Route ─────────────────────────────────────────────────────────────────────
if df is not None:
    render_workspace(df)
elif not has_data:
    render_welcome()
