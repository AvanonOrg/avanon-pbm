import asyncio
import logging
import re
from typing import Optional
from ruflo import browser

logger = logging.getLogger(__name__)

GOODRX_BASE = "https://www.goodrx.com"


async def scrape_goodrx(drug_name: str, strength: Optional[str] = None, quantity: int = 30) -> Optional[dict]:
    """Scrape lowest GoodRx price for a drug using ruflo browser tools."""
    slug = drug_name.lower().replace(" ", "-").replace("/", "-")
    url = f"{GOODRX_BASE}/{slug}"

    try:
        await browser.open_url(url)
        await browser.wait(2000)
        snapshot = await browser.snapshot()

        # Try to get text from price elements
        page_text = await browser.get_text()

        prices = _extract_prices_from_text(page_text)

        if not prices:
            logger.warning(f"No GoodRx prices found for {drug_name}")
            await browser.close()
            return None

        lowest = min(prices)
        await browser.close()

        return {
            "drug_name": drug_name,
            "source": "goodrx",
            "lowest_price": lowest,
            "prices_found": prices,
            "url": url,
            "quantity": quantity,
        }
    except Exception as e:
        logger.error(f"GoodRx scrape failed for '{drug_name}': {e}")
        try:
            await browser.close()
        except Exception:
            pass
        return None


def _extract_prices_from_text(text: str) -> list[float]:
    """Extract dollar amounts from page text."""
    pattern = r'\$(\d{1,4}(?:\.\d{2})?)'
    matches = re.findall(pattern, text)
    prices = []
    for m in matches:
        try:
            val = float(m)
            # Filter out obviously wrong values (< $1 or > $10000 for a prescription)
            if 1.0 < val < 10000.0:
                prices.append(val)
        except ValueError:
            pass
    return prices
