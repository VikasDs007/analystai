"""Above-the-fold AI summary and top data-quality issues."""

import html

import streamlit as st


def _severity_rank(issue):
    sev = issue.get("severity", "")
    if "High" in sev:
        return 0
    if "Medium" in sev:
        return 1
    return 2


def render_above_fold_summary(understanding, issues):
    """Show AI understanding above the tabs — issues are shown in the overview tab only."""
    safe_text = html.escape(str(understanding or ""))

    st.markdown(
        f"""
        <div class="above-fold-grid">
            <div class="above-fold-card understanding-card">
                <p class="above-fold-label">🤖 AI understanding</p>
                <p class="above-fold-body">{safe_text}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
