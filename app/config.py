"""Application paths and constants."""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CACHE_CSV = os.path.join(ROOT, ".analystai_last_upload.csv")
CACHE_STATE = os.path.join(ROOT, ".analystai_last_state.json")
CACHE_CLEAN_CSV = os.path.join(ROOT, ".analystai_last_cleaned.csv")
ONBOARD_FLAG = os.path.join(ROOT, ".analystai_onboarded")
SAMPLE_CSV = os.path.join(ROOT, "sample_data", "sample_sales.csv")

SESSION_KEYS = [
    "df_raw", "df_clean", "detective_result", "cleaning_report",
    "charts", "insights", "report", "qa_history", "last_file_id", "last_file_name",
    "filters", "anomalies", "custom_charts", "onboarding_seen",
    "cached_chart_specs", "qa_question_input", "clear_qa_question_input",
    "skip_cache_reload", "workspace_tab",
    "cleaning_decision", "cleaning_diff", "filters_dirty",
    "analysis_in_progress", "analysis_future", "analysis_start_ts",
    "analysis_est_seconds", "analysis_refresh_pending",
]


# Main workspace navigation (sidebar + top stepper stay in sync via workspace_tab)
WORKSPACE_TABS = [
    ("overview", "Overview"),
    ("quality", "Data quality"),
    ("charts", "Charts"),
    ("report", "Report"),
    ("ask", "Ask"),
]

WORKSPACE_TAB_KEYS = [key for key, _ in WORKSPACE_TABS]

PIPELINE_ARTIFACT_KEYS = [
    "df_raw", "df_clean", "detective_result", "charts", "insights", "report",
    "qa_history", "last_file_name", "filters", "cached_chart_specs",
]

UPLOAD_CLEAR_KEYS = [
    "df_raw", "df_clean", "detective_result", "cleaning_report",
    "charts", "insights", "report", "qa_history", "last_file_id", "last_file_name",
    "filters", "cached_chart_specs",
    "cleaning_decision", "cleaning_diff", "filters_dirty",
    "analysis_in_progress", "analysis_future", "analysis_start_ts",
    "analysis_est_seconds", "analysis_refresh_pending",
]


def setup_path():
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
