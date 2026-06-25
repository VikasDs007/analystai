import pandas as pd
import numpy as np
from agents.detective import detect_issues
from agents.cleaner import run_cleaner


def test_detect_and_clean_date_normalization():
    # Setup test dataframe with date represented as text
    df = pd.DataFrame({
        "order_date": ["01/02/2026", "02-03-2026", "2026/04/05", np.nan],
        "sales": [100, 200, 300, 400]
    })
    
    # 1. Detect
    issues = detect_issues(df)
    date_issues = [i for i in issues if i["type"] == "date_normalization"]
    assert len(date_issues) == 1
    assert date_issues[0]["column"] == "order_date"
    
    # 2. Clean - only pass date_normalization to avoid filling missing value first
    df_clean, report = run_cleaner(df, date_issues, use_llm=False)
    # The non-null dates should be normalized to YYYY-MM-DD
    assert df_clean.loc[0, "order_date"] == "2026-01-02"
    assert df_clean.loc[1, "order_date"] == "2026-02-03"
    assert df_clean.loc[2, "order_date"] == "2026-04-05"
    assert pd.isna(df_clean.loc[3, "order_date"])
    assert any("Normalized date formatting" in line for line in report)


def test_detect_and_clean_date_normalization_with_time():
    # Date text with time
    df = pd.DataFrame({
        "transaction_time": ["2026-01-01 10:15:30", "2026-01-02 12:00:00"],
        "sales": [10, 20]
    })
    issues = detect_issues(df)
    df_clean, report = run_cleaner(df, issues, use_llm=False)
    assert df_clean.loc[0, "transaction_time"] == "2026-01-01 10:15:30"
    assert df_clean.loc[1, "transaction_time"] == "2026-01-02 12:00:00"


def test_detect_and_clean_unnamed_or_empty_column():
    # Setup test dataframe with unnamed columns and empty columns
    df = pd.DataFrame({
        "Unnamed: 0": [1, 2, 3],
        "normal_col": ["a", "b", "c"],
        "empty_col": [np.nan, np.nan, np.nan]
    })
    
    # 1. Detect
    issues = detect_issues(df)
    unnamed_issues = [i for i in issues if i["type"] == "unnamed_or_empty_column"]
    assert len(unnamed_issues) == 2
    cols_detected = {i["column"] for i in unnamed_issues}
    assert "Unnamed: 0" in cols_detected
    assert "empty_col" in cols_detected
    
    # 2. Clean
    df_clean, report = run_cleaner(df, issues, use_llm=False)
    assert "Unnamed: 0" not in df_clean.columns
    assert "empty_col" not in df_clean.columns
    assert "normal_col" in df_clean.columns
    assert any("Dropped empty or unnamed column 'Unnamed: 0'" in line for line in report)
    assert any("Dropped empty or unnamed column 'empty_col'" in line for line in report)


def test_clean_existing_issues_smoke():
    # Test standard issues: duplicate rows, missing values, casing
    df = pd.DataFrame({
        "normal_col": ["Apple", "apple", "Banana", "Banana"],
        "num_col": [1.0, np.nan, 2.0, 2.0],
        "val_col": [10.0, 11.0, 12.0, 12.0]
    })
    
    issues = detect_issues(df)
    df_clean, report = run_cleaner(df, issues, use_llm=False)
    
    # Duplicate banana row should be removed (from 4 rows to 3)
    assert len(df_clean) == 3
    # Text casing standardized
    assert df_clean.loc[0, "normal_col"] == "Apple"
    assert df_clean.loc[1, "normal_col"] == "Apple"
    # Missing value filled with median
    assert not df_clean["num_col"].isnull().any()


def test_clean_outliers():
    # Capping outliers with a proper distribution where IQR > 0 and no duplicate rows
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "outlier_col": [1.0, 1.1, 1.2, 1.0, 1.1, 1.2, 1.0, 1.1, 100.0]
    })
    issues = detect_issues(df)
    outlier_issues = [i for i in issues if i["type"] == "outliers"]
    assert len(outlier_issues) == 1
    
    df_clean, report = run_cleaner(df, issues, use_llm=False)
    assert df_clean["outlier_col"].max() < 2.0
    assert any("Capped 1 extreme values" in line for line in report)
