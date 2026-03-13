from playwright.async_api import async_playwright
import asyncio

SEARCH_ENGINES = [
    "https://www.google.com/search?q=",
    "https://news.google.com/search?q=",
]

async def scrape_sources(claim: str, max_results: int = 5) -> list[dict]:
    """
    Uses Playwright to search for a news claim across the web
    and returns a list of sources with title, url, and snippet.
    """
    results = []
    query = claim.replace(" ", "+") + "+fact+check"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Set a real user agent to avoid blocks
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        try:
            await page.goto(
                f"https://www.google.com/search?q={query}",
                timeout=15000
            )
            await page.wait_for_timeout(2000)

            # Scrape search result cards
            cards = await page.query_selector_all("div.g")

            for card in cards[:max_results]:
                try:
                    title_el = await card.query_selector("h3")
                    link_el  = await card.query_selector("a")
                    desc_el  = await card.query_selector("div.VwiC3b")

                    title   = await title_el.inner_text() if title_el else "No title"
                    url     = await link_el.get_attribute("href") if link_el else ""
                    snippet = await desc_el.inner_text() if desc_el else ""

                    if url and url.startswith("http"):
                        results.append({
                            "title":   title,
                            "url":     url,
                            "snippet": snippet
                        })
                except Exception:
                    continue

        except Exception as e:
            print(f"[Scraper] Error: {e}")
        finally:
            await browser.close()

    return results


async def get_page_content(url: str, max_chars: int = 3000) -> str:
    """Fetch the full text content of a page for deeper AI analysis."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=15000)
            await page.wait_for_timeout(1500)
            content = await page.inner_text("body")
            return content[:max_chars]
        except Exception as e:
            return f"Could not fetch page: {e}"
        finally:
            await browser.close()
