"""Landing page hero banner."""

import streamlit as st
import streamlit.components.v1 as components


def render_hero():
    # ── App name + tagline hero ───────────────────────────────────────────────
    # Change 4: more specific, concrete tagline with a time claim
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
        '</div></div>',
        unsafe_allow_html=True,
    )

    # ── How it works — 4-step workflow ───────────────────────────────────────
    components.html(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
          * { box-sizing: border-box; font-family: 'Inter', sans-serif; }
          .steps-label {
            font-size: 0.7rem; font-weight: 700; letter-spacing: .1em;
            text-transform: uppercase; color: #6366F1; margin: 0 0 12px 0;
          }
          .steps-grid {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
          }
          .step-card {
            background: #FFFFFF; border: 1px solid #E2E8F0;
            border-radius: 12px; padding: 16px 18px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.06);
          }
          .step-icon { font-size: 1.6rem; margin-bottom: 8px; }
          .step-title { font-weight: 700; color: #0F172A; font-size: 0.9rem; margin-bottom: 5px; }
          .step-desc  { color: #64748B; font-size: 0.8rem; line-height: 1.5; margin: 0; }
        </style>

        <p class="steps-label">HOW IT WORKS — 4 SIMPLE STEPS</p>
        <div class="steps-grid">

          <div class="step-card" style="border-top: 3px solid #6366F1;">
            <div class="step-icon">📂</div>
            <div class="step-title">Step 1 — Upload your CSV</div>
            <p class="step-desc">Drop any spreadsheet — sales, inventory, surveys, finance. Up to 10 MB supported.</p>
          </div>

          <div class="step-card" style="border-top: 3px solid #0EA5E9;">
            <div class="step-icon">🧹</div>
            <div class="step-title">Step 2 — AI profiles &amp; cleans</div>
            <p class="step-desc">OpenAI detects missing values, duplicates and outliers — then fixes them automatically.</p>
          </div>

          <div class="step-card" style="border-top: 3px solid #10B981;">
            <div class="step-icon">📊</div>
            <div class="step-title">Step 3 — Explore charts &amp; KPIs</div>
            <p class="step-desc">AI picks the best charts for your data. Build custom ones in Chart Studio.</p>
          </div>

          <div class="step-card" style="border-top: 3px solid #F59E0B;">
            <div class="step-icon">🤖</div>
            <div class="step-title">Step 4 — Ask anything</div>
            <p class="step-desc">Type any question in plain English and get a specific, data-backed answer instantly.</p>
          </div>

        </div>
        """,
        height=200,
        scrolling=False,
    )
