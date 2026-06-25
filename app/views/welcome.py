"""Welcome screen shown below the upload zone on the landing page."""

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from app.config import SAMPLE_CSV


def render_welcome():
    # ── Change 5: Social proof / hackathon context strip ─────────────────────
    components.html(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
          * { box-sizing: border-box; font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
          .proof-bar {
            display: flex; align-items: center; justify-content: center;
            gap: 32px; flex-wrap: wrap;
            background: #F8FAFC; border: 1px solid #E2E8F0;
            border-radius: 12px; padding: 14px 24px;
            margin: 8px 0 20px 0;
          }
          .proof-item {
            display: flex; align-items: center; gap: 8px;
            font-size: 0.82rem; color: #475569; font-weight: 500;
          }
          .proof-icon { font-size: 1.1rem; }
          .proof-divider {
            width: 1px; height: 20px; background: #E2E8F0;
          }
        </style>
        <div class="proof-bar">
          <div class="proof-item">
            <span class="proof-icon">🏆</span>
            Built for the OpenAI Hackathon
          </div>
          <div class="proof-divider"></div>
          <div class="proof-item">
            <span class="proof-icon">🤖</span>
            Powered by GPT via OpenRouter
          </div>
          <div class="proof-divider"></div>
          <div class="proof-item">
            <span class="proof-icon">⚡</span>
            Full analysis in ~30 seconds
          </div>
          <div class="proof-divider"></div>
          <div class="proof-item">
            <span class="proof-icon">🔒</span>
            Your data stays in your session
          </div>
        </div>
        """,
        height=80,
        scrolling=False,
    )

    # ── Change 3: Sample data preview instead of redundant feature grid ───────
    try:
        sdf = pd.read_csv(SAMPLE_CSV)
        st.markdown(
            '<div style="margin:0.5rem 0 0.6rem 0;">'
            '<p style="font-size:0.72rem;font-weight:700;letter-spacing:.08em;'
            'text-transform:uppercase;color:#6366F1;margin:0 0 8px 0;">'
            'SAMPLE DATASET PREVIEW — 120 rows of retail sales data</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(sdf.head(6), width="stretch", height=200)
        st.caption("This is what AnalystAI will analyse — click **▶ Load sample data** above to try it instantly.")
    except Exception:
        pass

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="footer">'
        '<span>AnalystAI</span> · Data Intelligence Platform · '
        'Created by OpenAI Codex · Built with Streamlit'
        '</div>',
        unsafe_allow_html=True,
    )
