import uuid
from datetime import datetime
from typing import List
from storage.models import DrugPriceAnalysis, DiscrepancyReport, SpreadFlag


def build_report(
    query: str,
    tenant_id: str,
    analyses: List[DrugPriceAnalysis],
) -> DiscrepancyReport:
    report_id = f"rpt_{uuid.uuid4().hex[:12]}"
    flagged = [a for a in analyses if a.flag in (SpreadFlag.HIGH, SpreadFlag.CRITICAL)]
    total_savings = sum(a.annual_savings_100_members for a in analyses)

    if flagged:
        worst = max(flagged, key=lambda a: a.spread_pct)
        summary = (
            f"Identified {len(flagged)} high-spread drug(s). "
            f"Worst: {worst.drug_name} at {worst.spread_pct:,.0f}% above acquisition cost."
        )
    else:
        summary = "No major spread pricing discrepancies detected for the queried drugs."

    recommendation = _build_recommendation(analyses, total_savings)

    return DiscrepancyReport(
        report_id=report_id,
        tenant_id=tenant_id,
        generated_at=datetime.utcnow(),
        query=query,
        summary=summary,
        drugs=analyses,
        recommendation=recommendation,
        total_annual_savings_100_members=round(total_savings, 2),
    )


def _build_recommendation(analyses: List[DrugPriceAnalysis], total_savings: float) -> str:
    flagged = [a for a in analyses if a.flag in (SpreadFlag.HIGH, SpreadFlag.CRITICAL)]
    if not flagged:
        return "Pricing appears within acceptable range. Continue monitoring for changes."

    drug_list = ", ".join(a.drug_name for a in flagged[:3])
    rec = (
        f"Negotiate pass-through pricing contracts for: {drug_list}. "
        f"Switching to pass-through PBM contracts could save your plan "
        f"~${total_savings:,.0f}/year per 100 members on these drugs alone. "
    )

    # Add Medicaid citation if available
    cited = [a for a in flagged if a.medicaid_citation]
    if cited:
        rec += f"State Medicaid audits corroborate this pattern: {cited[0].medicaid_citation}"

    return rec
