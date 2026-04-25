from datetime import datetime

FLAG_LABELS = {
    "LOW": "Low Risk",
    "MEDIUM": "Medium Risk",
    "HIGH": "High Risk",
    "CRITICAL": "Critical",
}


def build_pdf_spec(report: dict) -> dict:
    drugs = report.get("drugs", [])

    generated_at = report.get("generated_at", datetime.utcnow().isoformat())
    if isinstance(generated_at, datetime):
        date_str = generated_at.strftime("%B %d, %Y")
    else:
        try:
            date_str = datetime.fromisoformat(str(generated_at)[:19]).strftime("%B %d, %Y")
        except Exception:
            date_str = str(generated_at)[:10]

    drug_table = {
        "title": "Drug Pricing Analysis — NADAC vs. Market Price",
        "after_section": 0,
        "headers": [
            "Drug", "Strength", "Qty",
            "NADAC Cost", "Market Price",
            "Spread $", "Spread %", "Risk Level",
            "Annual Savings / 100 Members",
        ],
        "rows": [],
    }
    for d in drugs:
        market = d.get("goodrx_lowest") or d.get("plan_price_estimate")
        drug_table["rows"].append([
            d.get("drug_name", ""),
            d.get("strength", "—"),
            str(d.get("quantity", 30)),
            f"${d.get('nadac_total', 0):.2f}",
            f"${market:.2f}" if market else "N/A",
            f"${d.get('spread_dollar', 0):.2f}",
            f"{d.get('spread_pct', 0):.1f}%",
            FLAG_LABELS.get(d.get("flag", "LOW"), d.get("flag", "")),
            f"${d.get('annual_savings_100_members', 0):,.0f}",
        ])

    spread_chart = {
        "type": "horizontal_bar",
        "title": "Spread Pricing by Drug (% Above NADAC Acquisition Cost)",
        "after_section": 1,
        "labels": [d.get("drug_name", "") for d in drugs],
        "datasets": [{"label": "Spread %", "values": [round(d.get("spread_pct", 0), 1) for d in drugs]}],
    }

    savings_chart = {
        "type": "bar",
        "title": "Estimated Annual Savings per 100 Members (Pass-Through vs. Spread Pricing)",
        "after_section": 2,
        "labels": [d.get("drug_name", "") for d in drugs],
        "datasets": [{"label": "Annual Savings ($)", "values": [round(d.get("annual_savings_100_members", 0)) for d in drugs]}],
    }

    citations = [
        f"{d['drug_name']}: {d['medicaid_citation']}"
        for d in drugs if d.get("medicaid_citation")
    ]
    citations_body = (
        "\n\n".join(citations)
        if citations
        else (
            "No state Medicaid audit citations are available for these specific drugs. "
            "For systemic context, refer to the Ohio Medicaid PBM Transparency Report (2018) — "
            "$224.8M spread on $2.5B spend — and the Kentucky CHFS PBM Audit Report (2019) — "
            "$123M retained by PBMs in spread pricing."
        )
    )

    return {
        "metadata": {
            "title": "PBM Spread Pricing Discrepancy Report",
            "subtitle": "Pharmacy Benefit Manager Pass-Through Intelligence Analysis",
            "author": "Avanon PBM Intelligence",
            "company": "Avanon",
            "department": "Benefits Analytics",
            "document_id": report.get("report_id", ""),
            "classification": "CONFIDENTIAL",
            "date": date_str,
            "page_size": "letter",
        },
        "executive_summary": (
            f"{report.get('summary', '')}\n\n"
            f"Total Estimated Annual Savings (100 Members): "
            f"${report.get('total_annual_savings_100_members', 0):,.0f}\n\n"
            f"Analysis Query: {report.get('query', '')}"
        ),
        "sections": [
            {
                "heading": "Drug Pricing Analysis",
                "body": (
                    f"The following {len(drugs)} drug(s) were analyzed for spread pricing discrepancies. "
                    "NADAC (National Average Drug Acquisition Cost) is the weekly CMS-published true "
                    "acquisition cost benchmark representing what pharmacies actually pay for drugs. "
                    "Any plan price materially above NADAC represents spread retained by the PBM "
                    "rather than passed through to the plan sponsor."
                ),
            },
            {
                "heading": "Spread Pricing Visualization",
                "body": (
                    "The chart below illustrates spread percentage by drug — the markup above the "
                    "NADAC acquisition cost benchmark. Drugs flagged as HIGH or CRITICAL represent "
                    "the most significant opportunities for savings under a pass-through contract."
                ),
            },
            {
                "heading": "Annual Savings Projection",
                "body": (
                    "Switching to a pass-through PBM contract eliminates spread on the drugs analyzed. "
                    "Savings below are modeled at 30-day supply per member, 12 months, across 100 plan members. "
                    "Actual savings scale linearly with membership size."
                ),
            },
            {
                "heading": "Regulatory Context",
                "body": citations_body,
            },
            {
                "heading": "Recommendations",
                "body": report.get("recommendation", ""),
            },
        ],
        "tables": [drug_table],
        "charts": [spread_chart, savings_chart],
        "theme": "navy",
    }
