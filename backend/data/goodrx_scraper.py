"""
GoodRx price lookup via direct HTTP — no Ruflo browser required.
GoodRx serves pricing JSON in a <script id="__NEXT_DATA__"> tag.
Falls back gracefully when unavailable.
"""
import json
import logging
import re
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

GOODRX_BASE = "https://www.goodrx.com"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def scrape_goodrx(
    drug_name: str,
    strength: Optional[str] = None,
    quantity: int = 30,
) -> Optional[dict]:
    slug = drug_name.lower().replace(" ", "-").replace("/", "-")
    url = f"{GOODRX_BASE}/{slug}"

    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=_HEADERS) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning(f"GoodRx HTTP {resp.status_code} for {drug_name}")
                return None

            html = resp.text

            # GoodRx embeds pricing in __NEXT_DATA__ JSON
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    prices = _extract_prices_from_next_data(data)
                    if prices:
                        lowest = min(prices)
                        return {
                            "drug_name": drug_name,
                            "source": "goodrx",
                            "lowest_price": lowest,
                            "prices_found": prices[:5],
                            "url": url,
                            "quantity": quantity,
                        }
                except (json.JSONDecodeError, KeyError):
                    pass

            # Fallback: parse dollar amounts from visible text
            prices = _extract_prices_from_text(html)
            if prices:
                lowest = min(prices)
                return {
                    "drug_name": drug_name,
                    "source": "goodrx",
                    "lowest_price": lowest,
                    "prices_found": prices[:5],
                    "url": url,
                    "quantity": quantity,
                }

            logger.warning(f"No GoodRx prices found for {drug_name}")
            return None

    except Exception as e:
        logger.error(f"GoodRx scrape failed for '{drug_name}': {e}")
        return None


def _extract_prices_from_next_data(data: dict) -> list[float]:
    """Walk the Next.js data tree looking for price-shaped numbers."""
    prices = []
    _walk(data, prices)
    return sorted(set(prices))


def _walk(obj: Any, out: list) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("price", "lowestPrice", "discountedPrice", "retailPrice") and isinstance(v, (int, float)):
                val = float(v)
                if 1.0 < val < 10000.0:
                    out.append(round(val, 2))
            else:
                _walk(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _walk(item, out)


def _extract_prices_from_text(html: str) -> list[float]:
    pattern = r'\$(\d{1,4}(?:\.\d{2})?)'
    prices = []
    for m in re.findall(pattern, html):
        try:
            val = float(m)
            if 1.0 < val < 10000.0:
                prices.append(val)
        except ValueError:
            pass
    return sorted(set(prices))


