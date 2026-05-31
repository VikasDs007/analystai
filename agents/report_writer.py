"""Report writer agent — turns the analysis outputs into a business report."""

from utils.helpers import get_llm_client, llm_json_decision


def run_report_writer(df, understanding: str, insights: str,
                      cleaning_report: list, stream: bool = False, use_llm=True,
                      kpis: list = None):
    """Return a markdown business report.

    When stream=True, returns a generator suitable for st.write_stream().
    kpis: list of KPI dicts with label/value/sub keys — injected into the prompt.
    """
    cleaning_text = (
        "\n".join(cleaning_report)
        if cleaning_report
        else "Data was already clean."
    )

    kpi_text = ""
    if kpis:
        kpi_lines = [f"- {k['label']}: {k['value']} ({k.get('sub', '')})" for k in kpis]
        kpi_text = "\nKEY METRICS:\n" + "\n".join(kpi_lines)

    context = (
        f"What the data is about:\n{understanding}\n"
        f"{kpi_text}\n\n"
        f"Data cleaning done:\n{cleaning_text}\n\n"
        f"Key findings from analysis:\n{insights}\n\n"
        f"Total records after cleaning: {len(df):,}"
    )

    report_plan = llm_json_decision(
        """
You are a cautious report planner.
Return only valid JSON with these keys:
{
  "sections": ["sections to include in the final report"],
  "risk_level": "low|medium|high",
  "confidence": 0.0,
  "guardrails": ["rules to avoid unsupported claims"]
}

Keep the plan grounded in the supplied analysis only.
""".strip(),
        context,
        max_tokens=400,
        temperature=0.1,
    )

    plan_text = ""
    if isinstance(report_plan, dict):
        sections = report_plan.get("sections", [])
        guardrails = report_plan.get("guardrails", [])
        plan_text = (
            f"Sections: {', '.join(sections) if sections else 'N/A'}\n"
            f"Guardrails: {', '.join(guardrails) if guardrails else 'N/A'}"
        )

    system_prompt = (
        "Write a professional business report for a small business owner based on the analysis below.\n\n"
        "Use this exact structure:\n\n"
        "## 📋 Overview\n"
        "(2–3 sentences on what the dataset contains, the business context, and the time period if available. "
        "Reference the actual record count and key metric names.)\n\n"
        "## 📊 Key Numbers\n"
        "(List the 3–4 most important KPI values from the KEY METRICS section. "
        "Format as: **Metric name**: value — one sentence explaining what it means for the business.)\n\n"
        "## 🧹 Data Quality\n"
        "(Bullet list of what was cleaned. If nothing was cleaned, say so in one sentence.)\n\n"
        "## 📈 Business Insights\n"
        "(3–4 bullets. Each must start with a specific number or percentage from the data. "
        "Explain what the pattern means in plain English. Do NOT repeat the quick-insights wording.)\n\n"
        "## ⚠️ Watch Points\n"
        "(1–2 risks or anomalies worth monitoring, grounded in the data.)\n\n"
        "## 🚀 Recommended Actions\n"
        "(3 concrete, specific actions. Each should reference an actual metric or category from the data.)\n\n"
        "## ✅ Summary\n"
        "(1–2 encouraging sentences summarising the overall picture.)\n\n"
        "Rules:\n"
        "- Use actual numbers from KEY METRICS and findings — never say 'significant' without a number\n"
        "- No jargon. Write for someone who has never seen a spreadsheet\n"
        "- Do not copy the quick-insights bullets verbatim\n"
        "- Target 500–600 words total\n"
        "- Warm, professional tone"
    )

    client = get_llm_client()

    def _generate():
        resp = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context}\n\nReport plan:\n{plan_text}"},
            ],
            max_tokens=900,
            temperature=0.4,
            stream=True,
        )
        for chunk in resp:
            delta = None
            if getattr(chunk, "choices", None):
                choice = chunk.choices[0]
                if getattr(choice, "delta", None):
                    delta = choice.delta.content
            if delta:
                yield delta

    if stream:
        return _generate()

    resp = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{context}\n\nReport plan:\n{plan_text}"},
        ],
        max_tokens=900,
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()
