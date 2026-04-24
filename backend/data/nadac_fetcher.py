import httpx
import logging
from typing import Optional
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

NADAC_API = "https://data.cms.gov/api/1/datastore/query/9778fb52-45c2-4df2-94f0-e3f5b50b8a8d/0"


async def fetch_nadac(drug_name: str, ndc: Optional[str] = None) -> Optional[dict]:
    """Fetch NADAC price from CMS. Returns per-unit price and metadata."""
    params = {"limit": 5, "offset": 0}
    if ndc:
        params["conditions[0][property]"] = "ndc"
        params["conditions[0][value]"] = ndc
        params["conditions[0][operator]"] = "="
    else:
        params["conditions[0][property]"] = "ndc_description"
        params["conditions[0][value]"] = drug_name
        params["conditions[0][operator]"] = "LIKE"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(NADAC_API, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                logger.warning(f"No NADAC results for '{drug_name}'")
                return None
            # Return the most recent result
            latest = results[0]
            return {
                "drug_name": latest.get("ndc_description", drug_name),
                "ndc": latest.get("ndc"),
                "nadac_per_unit": float(latest.get("nadac_per_unit", 0)),
                "effective_date": latest.get("effective_date"),
                "pricing_unit": latest.get("pricing_unit"),
                "otc": latest.get("otc"),
                "explanation_code": latest.get("explanation_code"),
            }
    except Exception as e:
        logger.error(f"NADAC fetch failed for '{drug_name}': {e}")
        return None


def calculate_total(nadac_per_unit: float, quantity: int) -> float:
    return round(nadac_per_unit * quantity, 2)
