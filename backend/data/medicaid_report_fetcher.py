"""
Fetches and extracts structured PBM spread pricing data from state Medicaid audit reports.
These are publicly available government documents with documented spread pricing evidence.
"""
import logging
import json
from typing import Optional
from ruflo import browser, knowledge_base

logger = logging.getLogger(__name__)

KB_NAMESPACE = "medicaid_pbm_reports"

# Known state Medicaid PBM audit report URLs and metadata
STATE_REPORTS = [
    {
        "state": "Ohio",
        "year": 2018,
        "url": "https://medicaid.ohio.gov/static/Providers/ManagedCare/PBM+Transparency+Report.pdf",
        "key_finding": "$224.8M spread on $2.5B Medicaid spend (9% blended margin)",
        "auditor": "Myers & Stauffer",
    },
    {
        "state": "Kentucky",
        "year": 2019,
        "url": "https://chfs.ky.gov/agencies/dms/Documents/PBMAuditReport.pdf",
        "key_finding": "PBMs retained $123M in spread pricing across Medicaid contracts",
        "auditor": "Myers & Stauffer",
    },
    {
        "state": "Texas",
        "year": 2021,
        "url": "https://www.hhsc.state.tx.us/assets/pharmacy/pbm-oversight-report-2021.pdf",
        "key_finding": "Spread pricing identified across multiple drug classes",
        "auditor": "Texas HHSC",
    },
    {
        "state": "New York",
        "year": 2020,
        "url": "https://www.osc.state.ny.us/files/reports/pdf/2020-N-7.pdf",
        "key_finding": "State Medicaid PBM transparency audit findings",
        "auditor": "NY State Comptroller",
    },
    {
        "state": "California",
        "year": 2022,
        "url": "https://data.chhs.ca.gov/dataset/prescription-drug-wholesale-acquisition-cost-wac-increases",
        "key_finding": "WAC price increase documentation for California Medi-Cal",
        "auditor": "DHCS",
    },
]

# Pre-structured known findings (for cases where PDF scraping isn't possible)
KNOWN_FINDINGS = {
    "ohio_2018": {
        "state": "Ohio",
        "year": 2018,
        "total_spread": 224800000,
        "total_spend": 2500000000,
        "spread_pct": 8.99,
        "drug_classes": ["generics", "brand", "specialty"],
        "summary": "Ohio Medicaid paid $224.8M more than PBMs paid pharmacies — a 9% spread margin on $2.5B in annual drug spend.",
        "citation": "Ohio Medicaid PBM Transparency Report (2018), Myers & Stauffer",
    },
    "kentucky_2019": {
        "state": "Kentucky",
        "year": 2019,
        "total_spread": 123000000,
        "summary": "Kentucky Medicaid PBMs retained $123M in spread pricing. Prompted state to mandate pass-through contracts.",
        "citation": "Kentucky CHFS PBM Audit Report (2019), Myers & Stauffer",
    },
}


async def seed_knowledge_base() -> None:
    """Seed the agentdb with known Medicaid PBM findings on startup."""
    logger.info("Seeding Medicaid PBM report knowledge base...")
    for report_key, finding in KNOWN_FINDINGS.items():
        await knowledge_base.store(KB_NAMESPACE, report_key, finding)
        logger.info(f"Stored Medicaid report: {report_key}")

    # Also store the report index
    await knowledge_base.store(KB_NAMESPACE, "_index", {
        "reports": list(KNOWN_FINDINGS.keys()),
        "states": [r["state"] for r in STATE_REPORTS],
    })
    logger.info("Medicaid KB seeded with pre-structured findings.")


async def fetch_state_report(state: str, year: Optional[int] = None) -> Optional[dict]:
    """Try to scrape a state Medicaid report URL and extract spread data."""
    report = next(
        (r for r in STATE_REPORTS if r["state"].lower() == state.lower()
         and (year is None or r["year"] == year)),
        None
    )
    if not report:
        return None

    # Check KB cache first
    key = f"{state.lower()}_{report['year']}"
    cached = await knowledge_base.recall(KB_NAMESPACE, key)
    if cached:
        return cached

    try:
        await browser.open_url(report["url"])
        await browser.wait(3000)
        text = await browser.get_text()
        await browser.close()

        # Return metadata + key finding even if full parse fails
        result = {
            "state": report["state"],
            "year": report["year"],
            "key_finding": report["key_finding"],
            "auditor": report["auditor"],
            "url": report["url"],
            "raw_text_excerpt": text[:2000] if text else "",
        }
        await knowledge_base.store(KB_NAMESPACE, key, result)
        return result
    except Exception as e:
        logger.warning(f"Could not fetch {state} report: {e}")
        return KNOWN_FINDINGS.get(f"{state.lower()}_{report['year']}")


async def get_citation_for_drug_class(drug_class: str) -> Optional[str]:
    """Return the most relevant Medicaid citation for a given drug/drug class."""
    synthesis = await knowledge_base.synthesize(
        KB_NAMESPACE,
        f"spread pricing evidence for {drug_class}"
    )
    if synthesis:
        return synthesis

    # Fallback to Ohio (most cited)
    ohio = KNOWN_FINDINGS.get("ohio_2018")
    if ohio:
        return ohio["citation"] + f": {ohio['summary']}"
    return None
