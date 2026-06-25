"""Shared layout components."""

import streamlit as st

def section(bg, icon, title):
    st.markdown(f"""<div class="sec-hdr">
        <div class="sec-icon" style="background:{bg};">{icon}</div>
        <p class="sec-title">{title}</p>
        <div class="sec-line"></div>
    </div>""", unsafe_allow_html=True)

def render_next_steps():
    """Render a simple next-steps guidance band."""
    return (
        """
    <div class="next-grid">
        <div class="next-card">
            <div class="next-ico">🔍</div>
            <div class="next-title">Detect patterns</div>
            <div class="next-desc">Review what AI found, then jump into the cleaned data preview for the details.</div>
        </div>
        <div class="next-card">
            <div class="next-ico">📊</div>
            <div class="next-title">Compare metrics</div>
            <div class="next-desc">Use Chart Studio to create a custom view or regenerate AI-picked charts.</div>
        </div>
        <div class="next-card">
            <div class="next-ico">🤖</div>
            <div class="next-title">Ask a question</div>
            <div class="next-desc">Use the suggested prompts or type your own to get a data-backed answer.</div>
        </div>
    </div>
    """
    )

def render_stat_cards(items):
    """Render snapshot items into HTML grid for `st.markdown`."""
    html = '<div class="snapshot-grid">'
    for it in items:
        cls = "snapshot-card primary" if it.get("color") == "primary" else "snapshot-card"
        html += f"<div class=\"{cls}\">"
        html += f"<div class=\"snapshot-lbl\">{it.get('label')}</div>"
        html += f"<div class=\"snapshot-val\">{it.get('value')}</div>"
        html += f"<div class=\"snapshot-sub\">{it.get('sub','')}</div>"
        html += "</div>"
    html += "</div>"
    return html


def progress_bar(step_index):
    """Render a simple progress bar indicating pipeline step progress."""
    try:
        steps = ["Profile", "Clean", "Charts", "Insights", "Report", "Ask"]
        html = '<div class="prog-bar">'
        for i, label in enumerate(steps):
            cls = 'prog-step'
            dot_cls = 'prog-dot'
            if i < step_index:
                cls += ' done'
                dot_cls += ' done'
            elif i == step_index:
                cls += ' active'
                dot_cls += ' active'
            html += f'<div class="{cls}"><span class="{dot_cls}"></span>{label}</div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
    except Exception:
        pass


def try_rerun():
    """Rerun the Streamlit app across versions."""
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
        return
    legacy = getattr(st, "experimental_rerun", None)
    if callable(legacy):
        legacy()


def render_skeleton(label="AI is working…", rows=3, show_chart=False):
    """Render a unified premium skeleton loading screen."""
    import streamlit.components.v1 as components

    is_dark = st.session_state.get("dark_mode", False)
    bg_base = "#0F172A" if is_dark else "#F8FAFC"
    border_color = "rgba(75, 85, 99, 0.2)" if is_dark else "#E2E8F0"
    
    bg_kpi_1 = "rgba(31, 41, 55, 0.6)" if is_dark else "rgba(248, 250, 252, 0.7)"
    bg_kpi_2 = "rgba(99, 102, 241, 0.16)" if is_dark else "rgba(99, 102, 241, 0.08)"
    
    bg_bar_1 = "rgba(31, 41, 55, 0.6)" if is_dark else "rgba(241, 245, 249, 0.7)"
    bg_bar_2 = "rgba(55, 65, 81, 0.7)" if is_dark else "rgba(226, 232, 240, 0.8)"
    
    bg_chart_1 = "rgba(31, 41, 55, 0.6)" if is_dark else "rgba(248, 250, 252, 0.7)"
    bg_chart_2 = "rgba(139, 92, 246, 0.16)" if is_dark else "rgba(238, 242, 255, 0.8)"
    
    text_color = "#A78BFA" if is_dark else "#6366F1"

    chart_block = ""
    if show_chart:
        chart_block = f"""
        <div class="sk-grid">
          <div class="sk-chart"></div>
          <div class="sk-chart"></div>
        </div>
        """

    bar_blocks = "".join(
        f'<div class="sk-bar" style="width:{w}%"></div>'
        for w in [85, 65, 50, 72, 40][:rows]
    )
    card_blocks = "".join(
        '<div class="sk-card"></div>' for _ in range(min(rows, 3))
    )

    components.html(
        f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
          * {{ box-sizing:border-box; font-family:'Inter',sans-serif; margin:0; padding:0; }}
          @keyframes shimmer {{
            0%   {{ background-position:-800px 0; }}
            100% {{ background-position: 800px 0; }}
          }}
          body {{ background: transparent; }}
          .sk-wrap  {{ padding:16px 0; }}
          .sk-label {{ font-size:0.82rem; font-weight:600; color:{text_color}; margin-bottom:14px;
                       display:flex; align-items:center; gap:8px; }}
          .sk-dot   {{ width:8px; height:8px; border-radius:50%; background:{text_color};
                       animation:pulse 1.2s ease-in-out infinite; }}
          @keyframes pulse {{
            0%,100% {{ opacity:1; transform:scale(1); }}
            50%      {{ opacity:0.4; transform:scale(0.7); }}
          }}
          .sk-kpi-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:16px; }}
          .sk-kpi {{
            border:1px solid {border_color}; border-radius:12px; height:72px;
            background:linear-gradient(90deg, {bg_kpi_1} 25%, {bg_kpi_2} 50%, {bg_kpi_1} 75%);
            background-size:800px 100%; animation:shimmer 1.4s infinite linear;
          }}
          .sk-bar {{
            height:13px; border-radius:7px; margin-bottom:11px;
            background:linear-gradient(90deg, {bg_bar_1} 25%, {bg_bar_2} 50%, {bg_bar_1} 75%);
            background-size:800px 100%; animation:shimmer 1.4s infinite linear;
          }}
          .sk-card {{
            border:1px solid {border_color}; border-radius:12px; height:58px; margin-bottom:10px;
            background:linear-gradient(90deg, {bg_kpi_1} 25%, {bg_bar_1} 50%, {bg_kpi_1} 75%);
            background-size:800px 100%; animation:shimmer 1.4s infinite linear;
          }}
          .sk-grid  {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-bottom:14px; }}
          .sk-chart {{
            border:1px solid {border_color}; border-radius:14px; height:200px;
            background:linear-gradient(90deg, {bg_chart_1} 25%, {bg_chart_2} 50%, {bg_chart_1} 75%);
            background-size:800px 100%; animation:shimmer 1.4s infinite linear;
          }}
        </style>
        <div class="sk-wrap">
          <div class="sk-label"><div class="sk-dot"></div>{label}</div>
          <div class="sk-kpi-grid">
            <div class="sk-kpi"></div><div class="sk-kpi"></div>
            <div class="sk-kpi"></div><div class="sk-kpi"></div>
          </div>
          {chart_block}
          {bar_blocks}
          {card_blocks}
        </div>
        """,
        height=320 if not show_chart else 560,
        scrolling=False,
    )

def render_data_in_use(df, df_clean):
    """Render a compact 'Data In Use' panel showing filename, counts, filters, and columns."""
    file_name = st.session_state.get("last_file_name") or st.session_state.get("last_file_id", "(in-memory)")
    filters = st.session_state.get("filters") or {}
    filters_txt = "None"
    if filters:
        parts = [f"{k}: {', '.join(map(str, v))}" for k, v in filters.items() if v]
        filters_txt = ", ".join(parts) if parts else "None"

    chips_html = "".join(
        f'<span style="background:#FFF;border:1px solid #E6EEF9;padding:6px 8px;'
        f'border-radius:10px;margin:4px;font-size:0.82rem;">{c}</span>'
        for c in list(df.columns[:24])
    )

    html = f"""
    <div style="display:flex;gap:18px;align-items:flex-start;margin:12px 0;">
        <div style="flex:1;min-width:260px;background:linear-gradient(180deg,#FFFFFF,#FBFCFF);border:1px solid #E8F0FF;padding:12px;border-radius:12px;">
            <div style="font-weight:700;color:#0F172A;margin-bottom:6px;">Current dataset</div>
            <div style="color:#334155;font-size:0.95rem;margin-bottom:6px;"><strong>File:</strong> {file_name}</div>
            <div style="color:#64748B;font-size:0.9rem;">Rows: <strong>{len(df):,}</strong> · Columns: <strong>{len(df.columns):,}</strong></div>
            <div style="color:#64748B;font-size:0.9rem;margin-top:6px;">Cleaned rows: <strong>{len(df_clean):,}</strong></div>
            <div style="color:#64748B;font-size:0.9rem;margin-top:8px;"><strong>Active filters:</strong> {filters_txt}</div>
        </div>
        <div style="flex:2;min-width:360px;background:#FFFFFF;border:1px solid #E8F0FF;padding:12px;border-radius:12px;">
            <div style="font-weight:700;color:#0F172A;margin-bottom:6px;">Columns (showing up to 24)</div>
            <div style="display:flex;flex-wrap:wrap;">{chips_html}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
