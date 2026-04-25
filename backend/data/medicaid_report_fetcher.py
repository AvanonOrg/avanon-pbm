"""
Pre-structured Medicaid PBM audit findings — no Ruflo dependency.
Uses in-process kb_cache for fast lookups.
"""
import logging
from typing import Optional

from storage import kb_cache

logger = logging.getLogger(__name__)

KB_NAMESPACE = "medicaid_pbm_reports"

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

STATE_REPORTS = [
    {"state": "Ohio", "year": 2018, "key_finding": "$224.8M spread on $2.5B Medicaid spend"},
    {"state": "Kentucky", "year": 2019, "key_finding": "PBMs retained $123M in spread pricing"},
    {"state": "Texas", "year": 2021, "key_finding": "Spread pricing identified across multiple drug classes"},
    {"state": "New York", "year": 2020, "key_finding": "State Medicaid PBM transparency audit findings"},
    {"state": "California", "year": 2022, "key_finding": "WAC price increase documentation for CA Medi-Cal"},
]


async def seed_knowledge_base() -> None:
    """Seed the in-process KB with known Medicaid PBM findings on startup."""
    logger.info("Seeding Medicaid PBM report knowledge base...")
    for report_key, finding in KNOWN_FINDINGS.items():
        await kb_cache.store(KB_NAMESPACE, report_key, finding)
        logger.info(f"Stored Medicaid report: {report_key}")
    await kb_cache.store(KB_NAMESPACE, "_index", {
        "reports": list(KNOWN_FINDINGS.keys()),
        "states": [r["state"] for r in STATE_REPORTS],
    })
    logger.info("Medicaid KB seeded with pre-structured findings.")


async def get_citation_for_drug_class(drug_name: str) -> Optional[str]:
    """Return the most relevant Medicaid citation for a given drug."""
    synthesis = await kb_cache.synthesize(KB_NAMESPACE, f"spread pricing evidence for {drug_name}")
    if synthesis:
        return synthesis
    ohio = KNOWN_FINDINGS.get("ohio_2018")
    if ohio:
        return ohio["citation"] + f": {ohio['summary']}"
    return None
