"""Ask-your-data panel (sidebar column on wide layouts)."""

import html
import time
import os
from pathlib import Path
import io

import streamlit as st

from agents.chat_box import handle_question
from app.ui.layout import section, try_rerun
import utils.helpers as helpers


def render_qa_panel(df_view, understanding, insights):
    section("#F0FDF4", "🤖", "Ask your data")
    st.markdown('<p class="ask-panel-hint">Ask in plain English — answers use your filtered dataset.</p>', unsafe_allow_html=True)

    # Chat header
    st.markdown(
        '<div class="chat-panel">'
        '<div class="chat-header">'
        '<div class="chat-title">🤖 Ask your data</div>'
        '<div class="chat-badge">AI Assistant</div>'
        '</div>'
        '<div class="chat-history" id="chat-history">',
        unsafe_allow_html=True,
    )

    # Live streaming indicator
    if st.session_state.get("qa_streaming"):
        st.markdown("<div style='padding:6px 10px;background:#FFF7ED;border:1px solid #FEEBC8;border-radius:8px;'>🤖 AI is typing…</div>", unsafe_allow_html=True)

    suggestions = helpers.suggest_questions(df_view)
    try:
        with st.expander("Example questions", expanded=False):
            if suggestions:
                st.markdown("**Based on your data:**")
                for q in suggestions:
                    st.markdown(f"- {q}")
    except Exception:
        pass
    if suggestions:
        for i, q in enumerate(suggestions[:4]):
            if st.button(q, key=f"ask_suggest_{i}", width="stretch"):
                _run_question(df_view, understanding, insights, q)

    # Render last messages from session history using Streamlit chat primitives
    if st.session_state.qa_history:
        history = st.session_state.qa_history
        start = max(0, len(history) - 12)
        for idx, entry in enumerate(history[start:], start=start):
            q = str(entry.get("q", ""))
            a = str(entry.get("a", ""))
            cites = entry.get("cites") or []
            plan = entry.get("plan")
            ts = entry.get("ts") or None
            if not ts:
                ts = entry.get("created_at") or None
            ts_str = ""
            try:
                import time as _time
                if ts:
                    ts_str = _time.strftime('%Y-%m-%d %H:%M:%S', _time.localtime(ts))
            except Exception:
                ts_str = ""

            # Render user message (premium bubble)
            try:
                user_html = "<div class='message user'><div class='avatar user'></div>"
                user_html += f"<div class='bubble user'>{html.escape(q)}</div>"
                user_html += "</div>"
                st.markdown(user_html, unsafe_allow_html=True)
                if ts_str:
                    st.markdown(f"<div class='msg-meta'>asked {ts_str}</div>", unsafe_allow_html=True)
            except Exception:
                st.markdown(f"**You:** {html.escape(q)}")

            # Render assistant message
            try:
                rendered = a and helpers.md_to_html(a) or ""
                ai_html = "<div class='message assistant'>"
                ai_html += "<div class='avatar assistant'>🤖</div>"
                ai_html += f"<div class='bubble assistant'>{rendered}</div>"
                ai_html += "</div>"
                st.markdown(ai_html, unsafe_allow_html=True)
                if cites:
                    st.markdown(f"<div class='msg-meta'>Sources: {', '.join(cites)}</div>", unsafe_allow_html=True)

                # 'Why this answer' details
                if plan:
                    try:
                        with st.expander("Why this answer", expanded=False):
                            if plan.get("primary_column"):
                                st.markdown(f"**Primary column:** {plan.get('primary_column')}")
                            if plan.get("secondary_column"):
                                st.markdown(f"**Secondary column:** {plan.get('secondary_column')}")
                            if plan.get("group_by_column"):
                                st.markdown(f"**Group by:** {plan.get('group_by_column')}")
                            if plan.get("required_columns"):
                                st.markdown(f"**Required columns:** {', '.join(plan.get('required_columns'))}")
                            if plan.get("calculation_plan"):
                                st.markdown(f"**Calculation plan:** {plan.get('calculation_plan')}")
                            if plan.get("guardrails"):
                                g = plan.get('guardrails')
                                if isinstance(g, list):
                                    for gline in g:
                                        st.markdown(f"- {gline}")
                                else:
                                    st.markdown(f"**Guardrails:** {g}")
                            if plan.get("confidence") is not None:
                                st.markdown(f"**Confidence:** {plan.get('confidence')}")
                    except Exception:
                        pass

                # per-message feedback/actions removed for a cleaner chat UI
            except Exception:
                st.markdown(f"**AI:** {html.escape(a)}")
                if cites:
                    st.markdown(f"**Sources:** {', '.join(cites)}")

    # close chat history div
    st.markdown('</div>', unsafe_allow_html=True)

    # Input: single-line text_input supports Enter to submit
    # Disable while streaming
    if st.session_state.get("qa_streaming"):
        disabled_input = True
    else:
        disabled_input = False

    question = st.text_input(
        "Ask a question",
        placeholder="Ask a question — e.g. Which region has the highest sales?",
        key="qa_question_input",
        disabled=disabled_input,
        label_visibility="collapsed",
    )
    # anchor for tour to highlight the ask box
    st.markdown('<div id="tour-ask-box" style="height:0px;width:0px;"></div>', unsafe_allow_html=True)

    # Submit by pressing Enter in the text_input or using the button
    submitted = False
    if (st.session_state.get("qa_question_input") or "").strip():
        # pressing Enter in text_input sets the value; capture via a small submit button next to it
        pass
    col1, col2 = st.columns([3,1])
    with col1:
        if st.button("Ask →", key="qa_submit_button", width="stretch", type="primary", disabled=disabled_input):
            submitted = True

    # Accept Enter key in text_input: streamlit triggers on_change, but we handle submit via button only.
    # If user entered a long question in the expander, prefer that when submitting.
    # Keep previous submit handling
    if submitted:
        q_text = (st.session_state.get("qa_question_input") or "").strip()
        if q_text:
            try:
                q_text = helpers.validate_user_question(q_text)
            except ValueError as ve:
                st.error(str(ve))
            else:
                _run_question(df_view, understanding, insights, q_text)
                # clear inputs
                st.session_state.qa_question_input = ""

    # close chat-panel wrapper
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.qa_history:
        if st.button("Clear chat", key="qa_clear", width="stretch"):
            st.session_state.qa_history = []
            try_rerun()


def _run_question(df_view, understanding, insights, question, answer_format=None):
    def _log_event(evt: str, payload: dict):
        try:
            p = Path("logs")
            p.mkdir(exist_ok=True)
            f = p / "qa.log"
            import json
            entry = {"ts": time.time(), "event": evt, "payload": payload}
            with open(f, "a") as fh:
                fh.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # support optional answer_format passed via kwargs in submit handlers
    import inspect
    caller_args = inspect.getcallargs(_run_question, df_view, understanding, insights, question) if False else {}
    # rate-limit: 2s per session
    last = st.session_state.get("qa_last_ts", 0)
    now = time.time()
    if now - last < 1.5:
        st.warning("Please wait a moment before asking another question.")
        return
    st.session_state["qa_last_ts"] = now
    # Stream the answer into the panel without triggering a full rerun.
    try:
        if st.session_state.qa_history is None:
            st.session_state.qa_history = []
        st.session_state.qa_history.append({"q": question, "a": "", "cites": [], "plan": None, "feedback": None})

        # mark streaming status so UI disables inputs
        st.session_state["qa_streaming"] = True

        # detect requested format (fallback to None)
        if answer_format:
            st.session_state["qa_answer_format"] = answer_format
        else:
            answer_format = st.session_state.get("qa_answer_format")

        _log_event("question_submitted", {"q": question})

        gen = None
        try:
            gen = handle_question(df_view, understanding, insights or "", question, stream=True, return_plan=True, answer_format=answer_format)
        except Exception:
            gen = handle_question(df_view, understanding, insights or "", question, stream=True, answer_format=answer_format)

        # If the agent returned (generator, plan) unpack it before iterating.
        plan = None
        answer_text = ""
        try:
            from types import GeneratorType
            if isinstance(gen, tuple) and len(gen) == 2:
                maybe_gen, maybe_plan = gen
                gen = maybe_gen
                plan = maybe_plan
        except Exception:
            pass
        # temporary placeholder while streaming (will be removed/replaced on rerun)
        placeholder = st.empty()

        from types import GeneratorType
        if isinstance(gen, GeneratorType) or hasattr(gen, "__next__"):
            if plan is None and hasattr(gen, "_answer_plan"):
                plan = getattr(gen, "_answer_plan")
            for chunk in gen:
                answer_text += str(chunk)
                # update the last history entry in-place so a subsequent rerun shows final text
                try:
                    st.session_state.qa_history[-1]["a"] = answer_text
                except Exception:
                    pass
                placeholder.markdown(
                    f'<div class="chat-msg"><div class="chat-av av-a">AI</div>'
                    f'<div class="chat-bub bub-a">{html.escape(answer_text)}</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            # synchronous return (possibly tuple(answer, plan))
            if isinstance(gen, tuple):
                answer_text, plan = gen
            else:
                answer_text = str(gen)
            st.session_state.qa_history[-1]["a"] = answer_text
            placeholder.markdown(
                f'<div class="chat-msg"><div class="chat-av av-a">AI</div>'
                f'<div class="chat-bub bub-a">{html.escape(answer_text)}</div></div>',
                unsafe_allow_html=True,
            )

        # assign plan and simple citations
        try:
            st.session_state.qa_history[-1]["plan"] = plan
        except Exception:
            pass

        cites = []
        cols = [c for c in df_view.columns.tolist()]
        low_q = question.lower()
        low_a = answer_text.lower()
        for c in cols:
            if c.lower() in low_q or c.lower() in low_a:
                cites.append(c)
        if not cites:
            try:
                from utils.helpers import choose_main_numeric
                main = choose_main_numeric([c for c in df_view.select_dtypes(include=["number"]).columns])
                if main:
                    cites = [main]
            except Exception:
                pass

        try:
            st.session_state.qa_history[-1]["cites"] = cites
        except Exception:
            pass

        # Logging final answer
        _log_event("question_answered", {"q": question, "answer_len": len(answer_text), "cites": cites})

        # clear streaming flag
        st.session_state["qa_streaming"] = False

        # remove transient placeholder and trigger final rerun to render history consistently
        try:
            placeholder.empty()
        except Exception:
            pass
        # Persist qa_history so it survives refresh
        try:
            from app.state.cache import save_cached_pipeline_state
            save_cached_pipeline_state()
        except Exception:
            pass
        try_rerun()
    except Exception as e:
        st.error(f"Could not answer: {e}")

