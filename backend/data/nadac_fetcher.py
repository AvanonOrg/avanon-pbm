import httpx
import logging
from typing import Optional
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

NADAC_API = "https://data.medicaid.gov/api/1/datastore/query/fbb83258-11c7-47f5-8b18-5f8e79f7e704/0"


async def fetch_nadac(drug_name: str, ndc: Optional[str] = None) -> Optional[dict]:
    """Fetch NADAC price from CMS. Returns per-unit price and metadata."""
    params = {"limit": 5, "offset": 0}
    if ndc:
        params["conditions[0][property]"] = "ndc"
        params["conditions[0][value]"] = ndc
        params["conditions[0][operator]"] = "="
    else:
        params["conditions[0][property]"] = "ndc_description"
        params["conditions[0][value]"] = f"%{drug_name}%"
        params["conditions[0][operator]"] = "LIKE"

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AvanonPBM/1.0)",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
            response = await client.get(NADAC_API, params=params)
            response.raise_for_status()
            if not response.content:
                logger.warning(f"Empty NADAC response for '{drug_name}'")
                return None
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
