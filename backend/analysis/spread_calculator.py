from storage.models import DrugPriceAnalysis, SpreadFlag
from typing import Optional


def calculate_spread(
    drug_name: str,
    nadac_per_unit: float,
    quantity: int,
    plan_price: Optional[float] = None,
    goodrx_lowest: Optional[float] = None,
    ndc: Optional[str] = None,
    strength: str = "",
    wac: Optional[float] = None,
    medicaid_citation: Optional[str] = None,
) -> DrugPriceAnalysis:
    nadac_total = round(nadac_per_unit * quantity, 2)

    # Use plan price if available, otherwise GoodRx as proxy
    comparison_price = plan_price or goodrx_lowest or 0.0

    spread_dollar = round(comparison_price - nadac_total, 2)
    spread_pct = round((spread_dollar / nadac_total) * 100, 1) if nadac_total > 0 else 0.0

    flag = _classify_spread(spread_pct)
    pass_through_savings = max(0.0, spread_dollar)
    annual_savings_100 = round(pass_through_savings * 12 * 100, 2)  # monthly * 12 months * 100 members

    return DrugPriceAnalysis(
        drug_name=drug_name,
        ndc=ndc,
        strength=strength,
        quantity=quantity,
        nadac_total=nadac_total,
        nadac_per_unit=nadac_per_unit,
        goodrx_lowest=goodrx_lowest,
        plan_price_estimate=plan_price,
        wac=wac,
        spread_dollar=spread_dollar,
        spread_pct=spread_pct,
        flag=flag,
        pass_through_savings=pass_through_savings,
        annual_savings_100_members=annual_savings_100,
        medicaid_citation=medicaid_citation,
    )


def _classify_spread(spread_pct: float) -> SpreadFlag:
    if spread_pct < 20:
        return SpreadFlag.LOW
    if spread_pct < 100:
        return SpreadFlag.MEDIUM
    if spread_pct < 500:
        return SpreadFlag.HIGH
    return SpreadFlag.CRITICAL


def format_savings_message(analysis: DrugPriceAnalysis) -> str:
    if analysis.flag in (SpreadFlag.HIGH, SpreadFlag.CRITICAL):
        return (
            f"{analysis.drug_name} {analysis.strength} {analysis.quantity}ct: "
            f"NADAC acquisition cost ${analysis.nadac_total:,.2f} vs "
            f"estimated plan price ${analysis.plan_price_estimate or analysis.goodrx_lowest:,.2f}. "
            f"Spread: ${analysis.spread_dollar:,.2f} ({analysis.spread_pct:,.0f}%). "
            f"Pass-through pricing saves ~${analysis.annual_savings_100_members:,.0f}/year for 100 plan members."
        )
    return (
        f"{analysis.drug_name}: ${analysis.nadac_total:,.2f} NADAC vs "
        f"${analysis.plan_price_estimate or analysis.goodrx_lowest:,.2f} plan price "
        f"({analysis.spread_pct:.1f}% spread)."
    )
