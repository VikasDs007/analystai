"""Chat box agent — answers questions from the analyzed dataset using LLM guidance and insights."""

import re

import pandas as pd

from utils.helpers import (
    build_data_context,
    choose_main_category,
    choose_main_numeric,
    get_llm_client,
    has_api_key,
    llm_json_decision,
)


def _text_stream(text, chunk_size=24):
    """Yield a text string in small chunks for Streamlit write_stream()."""
    if text is None:
        return
    text = str(text)
    for idx in range(0, len(text), chunk_size):
        yield text[idx:idx + chunk_size]


def _local_question_answer(df, question: str):
    """Try to answer common analytics questions without using the LLM."""
    import numpy as np

    def _norm(text: str) -> str:
        return re.sub(r"\s+", " ", str(text).replace("_", " ").strip().lower())

    def _match_column(question_text: str, columns: list):
        if not columns:
            return None
        qn = _norm(question_text)

        for col in columns:
            cn = _norm(col)
            if cn and cn in qn:
                return col

        q_tokens = set(re.findall(r"[a-z0-9]+", qn))
        best_col = None
        best_score = 0.0
        for col in columns:
            c_tokens = set(re.findall(r"[a-z0-9]+", _norm(col)))
            if not c_tokens:
                continue
            overlap = len(c_tokens & q_tokens)
            score = overlap / float(len(c_tokens))
            if score > best_score:
                best_score = score
                best_col = col
        return best_col if best_score >= 0.5 else None

    def _mentioned_columns(question_text: str, columns: list):
        qn = _norm(question_text)
        mentioned = []
        for col in columns:
            if _norm(col) in qn:
                mentioned.append(col)
        return mentioned

    def _extract_top_n(question_text: str, default=3):
        m = re.search(r"\btop\s+(\d+)\b", question_text.lower())
        if m:
            try:
                return max(1, int(m.group(1)))
            except Exception:
                pass
        words_to_n = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "ten": 10,
        }
        for word, value in words_to_n.items():
            if f"top {word}" in question_text.lower():
                return value
        return default

    lower_q = question.lower()
    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns]
    object_cols = [c for c in df.select_dtypes(include=["object"]).columns]

    if any(w in lower_q for w in ["product", "products"]) and any(w in lower_q for w in ["bad", "worst", "lowest", "bottom", "performing worst", "performing bad"]):
        if "Product" in df.columns or any(c.lower() == "product" for c in df.columns):
            gb = next((c for c in df.columns if c.lower() == "product"), "Product")
            if gb in df.columns and numeric_cols:
                primary_col = choose_main_numeric(numeric_cols)
                metric = pd.to_numeric(df[primary_col], errors="coerce")
                grouped = df.assign(_metric=metric).groupby(gb, dropna=False)["_metric"].sum()
                if not grouped.empty:
                    worst_name = grouped.idxmin()
                    worst_val = grouped.min()
                    return f"Lowest {primary_col.replace('_',' ')}: {worst_name} — {worst_val:,.2f}."

    if any(word in lower_q for word in ["how many rows", "number of rows", "records", "row count"]):
        return f"This filtered dataset has {len(df):,} rows."
    if any(word in lower_q for word in ["how many columns", "number of columns", "column count"]):
        return f"This filtered dataset has {df.shape[1]:,} columns."

    if not numeric_cols:
        return None

    target = _match_column(question, numeric_cols) or choose_main_numeric(numeric_cols)
    if not target:
        return None

    series = pd.to_numeric(df[target], errors="coerce")

    mentioned_numeric = _mentioned_columns(question, numeric_cols)
    group_col = _match_column(question, object_cols)

    if any(word in lower_q for word in ["correlation", "correlate", "relationship"]):
        pair = mentioned_numeric[:2]
        if len(pair) < 2 and len(numeric_cols) >= 2:
            pair = [target] + [c for c in numeric_cols if c != target][:1]
        if len(pair) == 2:
            corr = pd.to_numeric(df[pair[0]], errors="coerce").corr(
                pd.to_numeric(df[pair[1]], errors="coerce")
            )
            if pd.notna(corr):
                return (
                    f"Correlation between {pair[0].replace('_', ' ')} and "
                    f"{pair[1].replace('_', ' ')}: {corr:.2f}."
                )

    if any(word in lower_q for word in ["average", "mean", "avg"]):
        return f"Average {target.replace('_', ' ')}: {series.mean():,.2f}."
    if any(word in lower_q for word in ["total", "sum", "how much"]):
        return f"Total {target.replace('_', ' ')}: {series.sum():,.2f}."
    if any(word in lower_q for word in ["max", "highest"]):
        return f"Highest {target.replace('_', ' ')}: {series.max():,.2f}."
    if any(word in lower_q for word in ["min", "lowest"]):
        return f"Lowest {target.replace('_', ' ')}: {series.min():,.2f}."

    if any(word in lower_q for word in ["count", "how many"]):
        return f"Count of non-missing {target.replace('_', ' ')} values: {int(series.count()):,}."

    if any(word in lower_q for word in ["which", "top", "most", "highest", "lowest", "by"]):
        cat = group_col or choose_main_category(object_cols)
        if cat and cat in df.columns:
            agg = "mean" if any(word in lower_q for word in ["average", "mean", "avg"]) else "sum"
            grouped = df.groupby(cat)[target].agg(agg)

            if any(word in lower_q for word in ["lowest", "bottom"]):
                top_n = _extract_top_n(question, default=3)
                grouped = grouped.sort_values(ascending=True).head(top_n)
                lines = [
                    f"Bottom {top_n} {cat.replace('_', ' ')} by {target.replace('_', ' ')} "
                    f"({agg}):"
                ]
            else:
                top_n = _extract_top_n(question, default=3)
                grouped = grouped.sort_values(ascending=False).head(top_n)
                lines = [
                    f"Top {top_n} {cat.replace('_', ' ')} by {target.replace('_', ' ')} "
                    f"({agg}):"
                ]
            for name, value in grouped.items():
                lines.append(f"- {name}: {value:,.2f}")
            return "\n".join(lines)

    if any(word in lower_q for word in ["trend", "over time", "monthly", "daily", "yearly"]):
        date_candidates = [
            c for c in df.columns
            if "date" in c.lower() or "time" in c.lower() or "month" in c.lower() or "year" in c.lower()
        ]
        if date_candidates:
            date_col = _match_column(question, date_candidates) or date_candidates[0]
            dt = pd.to_datetime(df[date_col], errors="coerce")
            valid = dt.notna().sum()
            if valid > 1:
                work = pd.DataFrame({"_dt": dt, "_metric": pd.to_numeric(df[target], errors="coerce")}).dropna()
                if not work.empty:
                    freq = "M" if "month" in lower_q or "monthly" in lower_q else "D"
                    trend = work.groupby(work["_dt"].dt.to_period(freq))["_metric"].sum().sort_index()
                    if len(trend) >= 2:
                        first_v = float(trend.iloc[0])
                        last_v = float(trend.iloc[-1])
                        change = (last_v - first_v)
                        pct = (change / first_v * 100.0) if first_v != 0 else 0.0
                        direction = "up" if change > 0 else ("down" if change < 0 else "flat")
                        return (
                            f"{target.replace('_', ' ').title()} trend by {date_col.replace('_', ' ')} is {direction}. "
                            f"It changed from {first_v:,.2f} to {last_v:,.2f} ({pct:+.1f}%)."
                        )

    return None

def _insight_fallback(question: str, insights: str, understanding: str = ""):
    """Build a short grounded response when the LLM is unavailable."""
    insight_lines = []
    for raw_line in (insights or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^[-•*]\s*", "", line)
        line = re.sub(r"^\d+\.\s*", "", line)
        if line:
            insight_lines.append(line)

    if insight_lines:
        highlights = " ".join(insight_lines[:2])
        return (
            f"I couldn't reach the AI service just now, but the data still points to: {highlights} "
            f"If you want, I can narrow this down further for: {question.strip()}"
        )

    summary_bits = []
    if understanding:
        summary_bits.append(str(understanding).strip())
    if question:
        summary_bits.append(f"I can help interpret your question about {question.strip()}")
    if summary_bits:
        return " ".join(summary_bits) + "."
    return "I couldn't reach the AI service just now. Please try again in a moment."


def handle_question(df, understanding: str, insights: str,
                    question: str, stream: bool = False, use_llm=True, return_plan: bool = False,
                    answer_format: str = None):
    """Answer a natural language question about the dataframe."""
    local_answer = _local_question_answer(df, question)

    def _fmt(value):
        try:
            return f"{float(value):,.2f}" if float(value) != int(float(value)) else f"{int(float(value)):,}"
        except Exception:
            return str(value)

    def _extract_top_n_local(q, default=3):
        m = re.search(r"\btop\s+(\d+)\b", q)
        if m:
            try:
                return max(1, int(m.group(1)))
            except Exception:
                pass
        words_to_n = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "ten": 10}
        for word, value in words_to_n.items():
            if f"top {word}" in q:
                return value
        return default

    def _exact_answer(plan):
        if not isinstance(plan, dict):
            return None

        answer_type = (plan.get("answer_type") or "unknown").lower()
        primary = plan.get("primary_column") or choose_main_numeric([
            c for c in df.select_dtypes(include=["number"]).columns
        ])
        secondary = plan.get("secondary_column")
        group_by = plan.get("group_by_column") or choose_main_category([
            c for c in df.select_dtypes(include=["object"]).columns
        ])
        top_n = plan.get("top_n") or 3

        q_text = (question or "").lower()

        try:
            top_n = int(top_n)
        except Exception:
            top_n = _extract_top_n_local(q_text, default=top_n or 3)

        if answer_type in {"sum", "mean", "max", "min", "count", "top_n"} and primary in df.columns:
            series = pd.to_numeric(df[primary], errors="coerce")
            if group_by in df.columns:
                metric = pd.to_numeric(df[primary], errors="coerce")
                if any(w in q_text for w in ["average", "mean", "avg", "per"]):
                    agg = "mean"
                elif any(w in q_text for w in ["total", "sum", "revenue", "sales", "overall"]):
                    agg = "sum"
                else:
                    if any(w in (primary or "").lower() for w in ["revenue", "sales", "total"]):
                        agg = "sum"
                    else:
                        agg = "mean"

                grouped = getattr(df.assign(_metric=metric).groupby(group_by, dropna=False)["_metric"], agg)().sort_values(ascending=False)

                worst_words = ["worst", "worst-performing", "performing worst", "performing bad", "poor", "lowest", "performing poorly"]
                ask_worst = any(w in q_text for w in worst_words) or "performing" in q_text and "bad" in q_text

                if answer_type == "top_n" or ask_worst or any(k in q_text for k in ["which", "which products", "which product"]):
                    n = top_n or 3
                    if ask_worst or any(w in q_text for w in ["bottom", "lowest", "worst"]):
                        sel = grouped.sort_values(ascending=True).head(n)
                        header = f"Bottom {n} {group_by.replace('_',' ')} by {primary.replace('_',' ')} ({agg}):"
                    else:
                        sel = grouped.head(n)
                        header = f"Top {n} {group_by.replace('_',' ')} by {primary.replace('_',' ')} ({agg}):"
                    lines = [header]
                    for name, value in sel.items():
                        lines.append(f"- {name}: {_fmt(value)}")
                    result = "\n".join(lines)
                    return _text_stream(result) if stream else result

                if answer_type == "max":
                    name = grouped.idxmax()
                    value = grouped.max()
                    result = f"Highest {primary.replace('_', ' ')}: {name} — {_fmt(value)}."
                    return _text_stream(result) if stream else result
                if answer_type == "min":
                    name = grouped.idxmin()
                    value = grouped.min()
                    result = f"Lowest {primary.replace('_', ' ')}: {name} — {_fmt(value)}."
                    return _text_stream(result) if stream else result

            if answer_type == "sum":
                result = f"Total {primary.replace('_', ' ')}: {_fmt(series.sum())}."
                return _text_stream(result) if stream else result
            if answer_type == "mean":
                result = f"Average {primary.replace('_', ' ')}: {_fmt(series.mean())}."
                return _text_stream(result) if stream else result
            if answer_type == "max":
                idx = series.idxmax()
                result = f"Highest {primary.replace('_', ' ')}: {_fmt(series.max())} in row {idx + 1}."
                return _text_stream(result) if stream else result
            if answer_type == "min":
                idx = series.idxmin()
                result = f"Lowest {primary.replace('_', ' ')}: {_fmt(series.min())} in row {idx + 1}."
                return _text_stream(result) if stream else result
            result = f"Count of non-missing {primary.replace('_', ' ')} values: {int(series.count()):,}."
            return _text_stream(result) if stream else result

        if answer_type == "top_n" and primary in df.columns and group_by in df.columns:
            metric = pd.to_numeric(df[primary], errors="coerce")
            grouped = (
                df.assign(_metric=metric)
                  .groupby(group_by, dropna=False)["_metric"]
                  .sum()
                  .sort_values(ascending=False)
                  .head(int(top_n))
            )
            lines = [f"Top {int(top_n)} {group_by.replace('_', ' ')} by {primary.replace('_', ' ')}:"]
            for name, value in grouped.items():
                lines.append(f"- {name}: {_fmt(value)}")
            result = "\n".join(lines)
            return _text_stream(result) if stream else result

        if answer_type == "comparison" and primary in df.columns and secondary in df.columns:
            first = pd.to_numeric(df[primary], errors="coerce")
            second = pd.to_numeric(df[secondary], errors="coerce")
            result = (
                f"{primary.replace('_', ' ').title()} average: {_fmt(first.mean())}; "
                f"{secondary.replace('_', ' ').title()} average: {_fmt(second.mean())}."
            )
            return _text_stream(result) if stream else result

        if answer_type == "correlation" and primary in df.columns and secondary in df.columns:
            corr = pd.to_numeric(df[primary], errors="coerce").corr(
                pd.to_numeric(df[secondary], errors="coerce")
            )
            result = (
                f"Correlation between {primary.replace('_', ' ')} and {secondary.replace('_', ' ')}: "
                f"{corr:.2f}."
            )
            return _text_stream(result) if stream else result

        return None

    context = build_data_context(df, understanding)
    insight_context = (insights or "").strip() or "No quick insights have been generated yet."
    full_context = (
        f"{context}\n\n"
        f"QUICK INSIGHTS TO USE IN PLAIN ENGLISH:\n{insight_context}"
    )

    llm_active = use_llm and has_api_key()

    if llm_active:
        try:
            answer_plan = llm_json_decision(
                """
You are a cautious analytics decision engine.
Return only valid JSON with these keys:
{
  "answerable": true,
  "reason": "why the question can or cannot be answered from the data",
  "answer_type": "sum|mean|max|min|count|top_n|comparison|correlation|trend|text_summary|unknown",
  "primary_column": "main column to use if relevant",
  "secondary_column": "secondary column if relevant",
  "group_by_column": "column to group by for top_n or comparison",
  "top_n": 3,
  "required_columns": ["columns needed to answer"],
  "calculation_plan": "how to answer using the data",
  "guardrails": ["rules to avoid mistakes"],
  "confidence": 0.0
}

Be strict: if the question needs data that is missing or ambiguous, set "answerable" to false.
""".strip(),
                f"Question: {question}\n\nData context:\n{full_context}",
                max_tokens=500,
                temperature=0.1,
            )

            if isinstance(answer_plan, dict) and not answer_plan.get("answerable", True):
                reason = answer_plan.get("reason", "I cannot answer that confidently from the available data.")
                message = (
                    f"I can't answer that confidently from the available data. {reason}. "
                    "Try asking about columns or metrics that appear in the dataset."
                )
                if return_plan:
                    return (_text_stream(message) if stream else message), answer_plan
                return _text_stream(message) if stream else message
        except Exception as exc:
            error_msg = f"AI error: {exc}"
            if return_plan:
                return (_text_stream(error_msg) if stream else error_msg), {}
            return _text_stream(error_msg) if stream else error_msg

    if not llm_active:
        if local_answer:
            if return_plan:
                return (_text_stream(local_answer) if stream else local_answer), {}
            return _text_stream(local_answer) if stream else local_answer

        exact_answer = _exact_answer(answer_plan if llm_active else None)
        if exact_answer:
            if return_plan:
                return exact_answer, answer_plan if llm_active else {}
            return exact_answer

        if not use_llm:
            fallback = (
                "I can answer this from the dataset, but I need a clearer match to the columns or metrics first."
            )
            if return_plan:
                return fallback, {}
            return fallback

    guardrails = ""
    if isinstance(answer_plan, dict):
        guardrails = answer_plan.get("calculation_plan", "")
        required_columns = answer_plan.get("required_columns", [])
        if required_columns:
            guardrails += f"\nRequired columns: {', '.join(required_columns)}"

    client = get_llm_client()

    def _generate():
        try:
            user_content = (
                f"{full_context}\n\nQuestion: {question}\n\nDecision plan:\n{guardrails}"
            )
            if answer_format:
                user_content += f"\n\nAnswer format: {answer_format}"

            system_msg = (
                "You are a natural-language chat box for a data intelligence app. "
                "Answer using the quick insights first, then the supporting data context. "
                "Write like a helpful analyst explaining what the insight means, not like a spreadsheet dump. "
                "Use only the facts provided. Be concise, specific, and business-friendly. "
                "If the user requested bullets, return up to 3 bullets. No technical jargon."
            )

            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=180,
                temperature=0.3,
                stream=True,
            )
            yielded = False
            for chunk in resp:
                delta = None
                if getattr(chunk, "choices", None):
                    choice = chunk.choices[0]
                    if getattr(choice, "delta", None):
                        delta = choice.delta.content
                    elif getattr(choice, "message", None):
                        delta = getattr(choice.message, "content", None)
                if delta:
                    yielded = True
                    yield delta
            if not yielded:
                yield "I could not generate an answer. Please try rephrasing your question."
        except Exception as exc:
            fallback = local_answer or _insight_fallback(question, insights, understanding)
            yield fallback
    try:
        client = get_llm_client()
    except Exception:
        fallback = local_answer or _insight_fallback(question, insights, understanding)
        if return_plan:
            return fallback, answer_plan if 'answer_plan' in locals() else {}
        return fallback

    if stream:
        gen = _generate()
        if return_plan:
            setattr(gen, "_answer_plan", answer_plan)
        return gen

    try:
        user_content = (
            f"{full_context}\n\nQuestion: {question}\n\nDecision plan:\n{guardrails}"
        )
        if answer_format:
            user_content += f"\n\nAnswer format: {answer_format}"

        system_msg = (
            "You are a natural-language chat box for a data intelligence app. "
            "Answer using the quick insights first, then the supporting data context. "
            "Write like a helpful analyst explaining what the insight means, not like a spreadsheet dump. "
            "Use only the facts provided. Keep it concise and follow the requested Answer format when provided. "
            "No technical jargon."
        )

        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_content},
            ],
            max_tokens=180,
            temperature=0.3,
        )
        answer = resp.choices[0].message.content.strip()
        if return_plan:
            return answer, answer_plan
        return answer
    except Exception:
        fallback = local_answer or _insight_fallback(question, insights, understanding)
        if return_plan:
            return fallback, answer_plan
        return fallback


answer_chat_question = handle_question
