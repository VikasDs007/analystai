"""Before/after comparison UI for data cleaning."""

import pandas as pd
import streamlit as st


def compute_cleaning_diff(df_before, df_after, cleaning_report):
    """Build a summary dict comparing raw vs cleaned frames."""
    rows_before = len(df_before)
    rows_after = len(df_after)
    rows_removed = max(0, rows_before - rows_after)

    dtype_changes = []
    for col in df_before.columns:
        if col not in df_after.columns:
            continue
        before_dtype = str(df_before[col].dtype)
        after_dtype = str(df_after[col].dtype)
        if before_dtype != after_dtype:
            dtype_changes.append(
                {"column": col, "before": before_dtype, "after": after_dtype}
            )

    imputed_cols = []
    for col in df_before.columns:
        if col not in df_after.columns:
            continue
        null_before = int(df_before[col].isnull().sum())
        null_after = int(df_after[col].isnull().sum())
        if null_after < null_before:
            imputed_cols.append(
                {
                    "column": col,
                    "filled": null_before - null_after,
                    "before": null_before,
                    "after": null_after,
                }
            )

    sample_removed = pd.DataFrame()
    if rows_removed > 0:
        try:
            merged = df_before.merge(df_after, how="left", indicator=True)
            only_left = merged[merged["_merge"] == "left_only"]
            if not only_left.empty:
                sample_removed = only_left.drop(columns=["_merge"]).head(5)
            elif int(df_before.duplicated().sum()) > 0:
                sample_removed = df_before[df_before.duplicated(keep="first")].head(5)
        except Exception:
            sample_removed = df_before.tail(min(5, rows_removed))

    sample_imputed = pd.DataFrame()
    if imputed_cols:
        col = imputed_cols[0]["column"]
        mask = df_before[col].isnull()
        if mask.any():
            idx = df_before.index[mask][:5]
            sample_imputed = pd.DataFrame(
                {
                    "column": col,
                    "before": df_before.loc[idx, col].values,
                    "after": df_after.loc[idx, col].values,
                }
            )

    return {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_removed": rows_removed,
        "dtype_changes": dtype_changes,
        "imputed_cols": imputed_cols,
        "cleaning_report": list(cleaning_report or []),
        "sample_removed": sample_removed,
        "sample_imputed": sample_imputed,
    }


def render_cleaning_diff(diff):
    """Render side-by-side cleaning summary."""
    if not diff:
        return

    st.markdown("#### Cleaning changes")
    m1, m2, m3 = st.columns(3)
    m1.metric("Rows before", f"{diff['rows_before']:,}")
    m2.metric("Rows after", f"{diff['rows_after']:,}")
    m3.metric("Rows removed", f"{diff['rows_removed']:,}")

    left, right = st.columns(2)
    with left:
        st.markdown("**What changed**")
        if diff.get("cleaning_report"):
            for line in diff["cleaning_report"]:
                st.markdown(f"- {line.replace('✅', '').strip()}")
        else:
            st.caption("No automated changes were applied.")

        if diff.get("dtype_changes"):
            st.markdown("**Column type changes**")
            for ch in diff["dtype_changes"]:
                st.markdown(
                    f"- `{ch['column']}`: {ch['before']} → {ch['after']}"
                )

        if diff.get("imputed_cols"):
            st.markdown("**Missing values filled**")
            for item in diff["imputed_cols"][:6]:
                st.markdown(
                    f"- `{item['column']}`: {item['before']} → {item['after']} nulls "
                    f"({item['filled']} filled)"
                )

    with right:
        st.markdown("**Sample rows affected**")
        sample_removed = diff.get("sample_removed")
        if isinstance(sample_removed, pd.DataFrame) and not sample_removed.empty:
            st.caption("Rows removed (sample)")
            st.dataframe(sample_removed, use_container_width=True, height=180)
        else:
            st.caption("No duplicate rows were removed.")

        sample_imputed = diff.get("sample_imputed")
        if isinstance(sample_imputed, pd.DataFrame) and not sample_imputed.empty:
            st.caption("Imputed values (sample)")
            st.dataframe(sample_imputed, use_container_width=True, height=180)
