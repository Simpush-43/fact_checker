import requests
from bs4 import BeautifulSoup


def _scrape(claim: str, max_results: int = 5) -> list:
    results = []
    query = claim.replace(" ", "+") + "+fact+check"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(
            f"https://www.google.com/search?q={query}",
            headers=headers, timeout=10
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div.g")
        for card in cards[:max_results]:
            try:
                title = card.select_one("h3").text if card.select_one("h3") else "No title"
                url   = card.select_one("a")["href"] if card.select_one("a") else ""
                desc  = card.select_one("div.VwiC3b")
                snippet = desc.text if desc else ""
                if url.startswith("http"):
                    results.append({"title": title, "url": url, "snippet": snippet})
            except Exception:
                continue
    except Exception as e:
        print(f"[Scraper] Error: {e}")
    return results


async def scrape_sources(claim: str, max_results: int = 5) -> list:
    return _scrape(claim, max_results)