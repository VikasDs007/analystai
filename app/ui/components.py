"""Reusable UI components for AnalystAI — Card, Badge, KPI, Dark Mode, Confetti, FAB."""

import streamlit as st
import streamlit.components.v1 as components


# ── Card Component ────────────────────────────────────────────────────────────

def card(content_html: str, *, padding: str = "1.2rem 1.4rem", hover: bool = True, accent: str = None):
    """Render a styled card wrapper around HTML content.

    Args:
        content_html: Inner HTML content.
        padding: CSS padding value.
        hover: Enable hover lift effect.
        accent: Optional top border color (CSS value).
    """
    hover_style = "transition:transform .2s,box-shadow .2s;cursor:default;" if hover else ""
    hover_effect = "onmouseover=\"this.style.transform='translateY(-2px)';this.style.boxShadow='0 12px 26px rgba(15,23,42,0.08)'\" onmouseout=\"this.style.transform='';this.style.boxShadow=''" if hover else ""
    accent_border = f"border-top:3px solid {accent};" if accent else ""
    st.markdown(
        f'<div style="background:var(--bg-surface);border:1px solid var(--border);'
        f'border-radius:var(--radius-md);padding:{padding};box-shadow:var(--shadow-sm);'
        f'{accent_border}{hover_style}" {hover_effect}>'
        f'{content_html}</div>',
        unsafe_allow_html=True,
    )


def card_grid(items: list[dict], *, columns: int = 3):
    """Render a grid of cards. Each item dict has 'icon', 'title', 'desc' keys."""
    cols = st.columns(columns)
    for i, item in enumerate(items):
        with cols[i % columns]:
            card(
                f'<div style="font-size:1.8rem;margin-bottom:10px;">{item.get("icon", "")}</div>'
                f'<div style="font-weight:600;color:var(--text-secondary);font-size:0.95rem;margin-bottom:6px;">'
                f'{item.get("title", "")}</div>'
                f'<div style="font-size:0.82rem;color:var(--text-muted);line-height:1.5;">'
                f'{item.get("desc", "")}</div>',
                hover=True,
            )


# ── Badge Component ───────────────────────────────────────────────────────────

def badge(text: str, variant: str = "default", *, size: str = "sm"):
    """Return HTML for a badge/pill element.

    Variants: default, primary, success, warning, danger, info.
    Sizes: sm, md.
    """
    colors = {
        "default": ("var(--bg-muted)", "var(--text-muted)", "var(--border)"),
        "primary": ("var(--primary-bg)", "var(--primary)", "var(--primary-border)"),
        "success": ("var(--success-bg)", "#16A34A", "var(--success-border)"),
        "warning": ("var(--warning-bg)", "#D97706", "var(--warning-border)"),
        "danger":  ("var(--danger-bg)", "var(--danger)", "var(--danger-border)"),
        "info":    ("#EFF6FF", "#3B82F6", "#BFDBFE"),
    }
    bg, fg, border = colors.get(variant, colors["default"])
    padding = "3px 10px" if size == "sm" else "5px 14px"
    font_size = "0.7rem" if size == "sm" else "0.8rem"
    return (
        f'<span style="background:{bg};color:{fg};border:1px solid {border};'
        f'border-radius:var(--radius-full);padding:{padding};font-size:{font_size};'
        f'font-weight:600;text-transform:uppercase;letter-spacing:.04em;white-space:nowrap;">'
        f'{text}</span>'
    )


def severity_badge(severity: str):
    """Render a severity badge (High/Medium/Low)."""
    if "High" in severity:
        return badge("High", "danger")
    if "Medium" in severity:
        return badge("Medium", "warning")
    return badge("Low", "success")


# ── Animated KPI Counter ─────────────────────────────────────────────────────

def kpi_card_animated(label: str, value: str, *, sub: str = "", icon: str = "",
                       color: str = "kpi-blue", animate: bool = True):
    """Render a KPI card with optional count-up animation.

    The animation uses JavaScript to count from 0 to the target value.
    """
    # Extract numeric value for animation
    numeric_str = value.replace(",", "").replace("%", "").replace("K", "000").replace("M", "000000")
    try:
        numeric_val = float(numeric_str)
    except (ValueError, TypeError):
        numeric_val = None

    target_id = f"kpi_{label.replace(' ', '_').lower()}"

    if animate and numeric_val is not None and numeric_val > 0:
        suffix = ""
        if "%" in value:
            suffix = "%"
        elif "K" in value:
            suffix = "K"
        elif "M" in value:
            suffix = "M"

        components.html(
            f"""<link href="https://fonts.googleapis.com/css2?family=Inter:wght@700&display=swap" rel="stylesheet">
            <style>
              .kpi-wrap {{ background:var(--bg-surface);border-radius:var(--radius-md);
                padding:1.1rem 1.3rem;border:1px solid var(--border);box-shadow:var(--shadow-sm);
                position:relative;overflow:hidden; }}
              .kpi-wrap::before {{ content:'';position:absolute;top:0;left:0;right:0;height:3px;
                background:linear-gradient(90deg,{_kpi_color_start(color)},{_kpi_color_end(color)}); }}
              .kpi-l {{ font-size:0.7rem;font-weight:600;text-transform:uppercase;
                letter-spacing:.08em;color:var(--text-faint);margin-bottom:4px; }}
              .kpi-v {{ font-size:1.9rem;font-weight:700;color:var(--text-primary);line-height:1;
                font-family:'Inter',sans-serif; }}
              .kpi-s {{ font-size:0.72rem;color:var(--text-muted);margin-top:4px; }}
              .kpi-i {{ font-size:1.4rem;float:right;margin-top:-2px;opacity:.7; }}
            </style>
            <div class="kpi-wrap">
              <div class="kpi-l">{label} <span class="kpi-i">{icon}</span></div>
              <div class="kpi-v" id="{target_id}">0{suffix}</div>
              <div class="kpi-s">{sub}</div>
            </div>
            <script>
            (function() {{
              const el = document.getElementById('{target_id}');
              if (!el) return;
              const target = {numeric_val};
              const suffix = '{suffix}';
              const duration = 1200;
              const start = performance.now();
              function fmt(n) {{
                if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
                if (n >= 1000) return (n/1000).toFixed(1) + 'K';
                if (suffix === '%') return n.toFixed(1) + '%';
                return n.toLocaleString();
              }}
              function step(now) {{
                const elapsed = now - start;
                const progress = Math.min(elapsed / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = eased * target;
                el.textContent = fmt(current) + (suffix && suffix !== '%' && suffix !== 'K' && suffix !== 'M' ? '' : '');
                if (progress < 1) requestAnimationFrame(step);
                else el.textContent = '{value}';
              }}
              requestAnimationFrame(step);
            }})();
            </script>""",
            height=100,
            scrolling=False,
        )
    else:
        # Non-animated fallback
        st.markdown(
            f'<div class="kpi-card {color}">'
            f'<div class="kpi-lbl">{label}<span class="kpi-ico">{icon}</span></div>'
            f'<div class="kpi-val">{value}</div>'
            f'<div class="kpi-sub">{sub}</div></div>',
            unsafe_allow_html=True,
        )


def _kpi_color_start(color_class: str) -> str:
    mapping = {
        "kpi-blue": "#3B82F6", "kpi-green": "#10B981", "kpi-purple": "#8B5CF6",
        "kpi-amber": "#F59E0B", "kpi-rose": "#F43F5E",
    }
    return mapping.get(color_class, "#3B82F6")


def _kpi_color_end(color_class: str) -> str:
    mapping = {
        "kpi-blue": "#60A5FA", "kpi-green": "#34D399", "kpi-purple": "#A78BFA",
        "kpi-amber": "#FCD34D", "kpi-rose": "#FB7185",
    }
    return mapping.get(color_class, "#60A5FA")


# ── Dark Mode Toggle ─────────────────────────────────────────────────────────

def render_dark_mode_toggle():
    """Render a dark mode toggle in the top-right area of the page."""
    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    # Use a button for toggle
    dark = st.session_state.get("dark_mode", False)
    icon = "☀️" if dark else "🌙"
    label = "Light" if dark else "Dark"
    if st.button(f"{icon} {label}", key="dark_mode_toggle", help="Toggle dark mode"):
        st.session_state.dark_mode = not dark
        st.rerun()


# ── Confetti ──────────────────────────────────────────────────────────────────

def render_confetti():
    """Render a confetti animation overlay. Call once when analysis completes."""
    import random
    colors = ["#6366F1", "#0EA5E9", "#10B981", "#F59E0B", "#F43F5E", "#8B5CF6", "#EC4899"]
    pieces = []
    for i in range(40):
        color = random.choice(colors)
        left = random.randint(0, 100)
        delay = random.uniform(0, 2)
        size = random.randint(6, 12)
        rotation = random.randint(0, 360)
        pieces.append(
            f'<div class="confetti-piece" style="left:{left}%;background:{color};'
            f'width:{size}px;height:{size}px;animation-delay:{delay:.1f}s;'
            f'border-radius:{"50%" if random.random() > 0.5 else "2px"};'
            f'transform:rotate({rotation}deg);"></div>'
        )
    html = f'<div style="position:fixed;inset:0;pointer-events:none;z-index:99999;">{"".join(pieces)}</div>'
    components.html(html, height=0, scrolling=False)


# ── Floating Action Button ────────────────────────────────────────────────────

def render_fab(*, on_regenerate=None, on_ask=None):
    """Render a floating action button cluster in the bottom-right corner.

    Args:
        on_regenerate: Callback or True to show regenerate button.
        on_ask: Callback or True to show ask AI button.
    """
    show_regen = on_regenerate is not None
    show_ask = on_ask is not None

    if not show_regen and not show_ask:
        return

    buttons_html = ""
    if show_ask:
        buttons_html += (
            '<button class="fab fab-secondary" onclick="window.parent.postMessage({type:\'streamlit:rerun\'},\'*\')" '
            'title="Ask AI">🤖</button>'
        )
    if show_regen:
        buttons_html += (
            '<button class="fab fab-primary" onclick="window.parent.postMessage({type:\'streamlit:rerun\'},\'*\')" '
            'title="Regenerate">🔄</button>'
        )

    components.html(
        f'<div class="fab-container">{buttons_html}</div>',
        height=0,
        scrolling=False,
    )


# ── Confirmation Dialog ───────────────────────────────────────────────────────

def confirm_dialog(title: str, message: str, confirm_label: str = "Confirm",
                    cancel_label: str = "Cancel", key: str = "confirm"):
    """Show a confirmation dialog. Returns True if confirmed, False if cancelled, None if pending."""
    if f"{key}_result" not in st.session_state:
        st.session_state[f"{key}_result"] = None

    if st.session_state[f"{key}_result"] is not None:
        result = st.session_state[f"{key}_result"]
        st.session_state[f"{key}_result"] = None
        return result

    col1, col2 = st.columns([3, 1])
    with col1:
        st.warning(f"**{title}** — {message}")
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            if st.button(confirm_label, key=f"{key}_yes", type="primary"):
                st.session_state[f"{key}_result"] = True
                st.rerun()
        with c2:
            if st.button(cancel_label, key=f"{key}_no"):
                st.session_state[f"{key}_result"] = False
                st.rerun()
    return None


# ── Page Transition Wrapper ───────────────────────────────────────────────────

def page_transition(key: str = "default"):
    """Wrap content in a fade-in animation div. Use as a container."""
    st.markdown(
        f'<div class="tab-content-enter" style="animation:fadeInUp 0.35s ease-out;">',
        unsafe_allow_html=True,
    )


def page_transition_end():
    """Close the page transition wrapper."""
    st.markdown("</div>", unsafe_allow_html=True)
