"""First-run onboarding modal."""

import os

import streamlit as st

from app.config import ONBOARD_FLAG
from app.ui.layout import try_rerun


def render_onboarding():
    if not st.session_state.get("onboarding_seen"):
        try:
            if os.path.exists(ONBOARD_FLAG):
                st.session_state.onboarding_seen = True
            else:
                try:
                    with st.modal("Welcome to AnalystAI", key="onboard_modal"):
                        st.markdown("""
                        ### Welcome 🎉
                        AnalystAI helps you analyse CSVs, clean data, build charts, and ask questions — all powered by OpenAI.

                        Quick tour:
                        - Upload a CSV or click **Sample Data** to start.
                        - OpenAI will profile your data, auto-clean issues, and suggest the best charts.
                        - Use **Chart Studio** to build custom charts and **Ask Your Data** for plain-English Q&A.

                        Click **Got it** to continue — this message will not appear again on this machine.
                        """)
                        if st.button("Got it — start analyzing"):
                            try:
                                open(ONBOARD_FLAG, "w").write("onboarded")
                            except Exception:
                                pass
                            st.session_state.onboarding_seen = True
                            try_rerun()
                except Exception:
                    with st.expander("Welcome to AnalystAI — Quick Tour", expanded=True):
                        st.markdown("""
                        - Upload a CSV or click **Sample Data** to start.
                        - OpenAI profiles, cleans, and visualises your data automatically.
                        - Use **Chart Studio** to build custom charts and **Ask Your Data** for plain-English Q&A.
                        """)
                        if st.button("Got it — start analyzing (expander)"):
                            try:
                                open(ONBOARD_FLAG, "w").write("onboarded")
                            except Exception:
                                pass
                            st.session_state.onboarding_seen = True
                            try_rerun()
        except Exception:
            st.session_state.onboarding_seen = True