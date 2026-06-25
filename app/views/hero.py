"""Landing page hero banner."""

import streamlit as st
import streamlit.components.v1 as components


def render_hero():
    # ── App name + tagline hero ───────────────────────────────────────────────
    st.markdown(
        '<div class="hero">'
        '<div style="display:flex;align-items:center;gap:14px;margin-bottom:0.5rem;">'
        '<span style="font-size:2rem;position:relative;z-index:1;">📊</span>'
        '<div style="position:relative;z-index:1;">'
        '<div style="font-size:0.7rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#93C5FD;margin-bottom:2px;">OpenAI Hackathon Project</div>'
        '<div class="hero-title" style="font-size:2.5rem;margin:0;line-height:1.1;">AnalystAI</div>'
        '</div></div>'
        '<div class="hero-sub" style="position:relative;z-index:1;font-size:1.08rem;margin-bottom:0.6rem;line-height:1.55;">'
        'Upload a CSV. Get a full business analysis in 30 seconds.<br>'
        '<span style="font-size:0.9rem;color:#64748B;">'
        'AI cleans your data, picks the best charts, writes a report, and answers your questions — no code needed.'
        '</span>'
        '</div>'
        '<div style="position:relative;z-index:1;">'
        '<span class="hero-badge">⚡ Created by OpenAI Codex</span>'
        '<span class="hero-badge">📊 Auto-Visualisation</span>'
        '<span class="hero-badge">🔽 Live Filters</span>'
        '<span class="hero-badge">🤖 AI Q&amp;A</span>'
        '<span class="hero-badge">🧹 Auto Data Cleaning</span>'
        '</div>'
        '<div style="position:relative;z-index:1;">'
        '<a href="#upload-section" class="hero-cta" style="text-decoration:none;">'
        '🚀 Start Analyzing — Upload CSV'
        '</a>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── How it works — 4-step workflow ───────────────────────────────────────
    st.markdown(
        """
        <div style="margin-top: 2rem;"></div>
        <p class="sb-section-label" style="letter-spacing: .08em; font-weight: 700; color: var(--text-muted);">HOW IT WORKS — 4 SIMPLE STEPS</p>
        <div class="feat-grid" style="grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));">

          <div class="feat-card" style="border-top: 3px solid #6366F1;">
            <div class="sb-num" style="background:#6366F1; margin-bottom: 8px;">1</div>
            <div class="feat-ico">📂</div>
            <div class="feat-ttl">Upload your dataset</div>
            <p class="feat-dsc">Drop any spreadsheet — CSV, Excel or JSON up to 10 MB. Flat tables work best.</p>
          </div>

          <div class="feat-card" style="border-top: 3px solid #0EA5E9;">
            <div class="sb-num" style="background:#0EA5E9; margin-bottom: 8px;">2</div>
            <div class="feat-ico">🧹</div>
            <div class="feat-ttl">AI profiles &amp; cleans</div>
            <p class="feat-dsc">OpenAI detects missing values, duplicates, and outliers — and lets you choose what to fix.</p>
          </div>

          <div class="feat-card" style="border-top: 3px solid #10B981;">
            <div class="sb-num" style="background:#10B981; margin-bottom: 8px;">3</div>
            <div class="feat-ico">📊</div>
            <div class="feat-ttl">Explore charts &amp; KPIs</div>
            <p class="feat-dsc">AI automatically selects the 6 best charts for your data. Customize them in Chart Studio.</p>
          </div>

          <div class="feat-card" style="border-top: 3px solid #F59E0B;">
            <div class="sb-num" style="background:#F59E0B; margin-bottom: 8px;">4</div>
            <div class="feat-ico">🤖</div>
            <div class="feat-ttl">Ask anything</div>
            <p class="feat-dsc">Type any question in plain English and get a specific, data-backed answer with citations.</p>
          </div>

        </div>
        """,
        unsafe_allow_html=True,
    )
