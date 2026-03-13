import google.generativeai as genai
import os
import json
from app.scraper import scrape_sources

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


SYSTEM_PROMPT = """
You are a professional fact-checking AI agent. You will be given:
1. A news headline or claim
2. A list of sources found on the web about this claim

Your job is to:
- Analyze all sources carefully
- Determine if the claim is TRUE, FALSE, MISLEADING, or UNVERIFIED
- Give a credibility score from 0 to 100 (100 = definitely true)
- Write a short explanation (2-3 sentences)
- List which sources support or contradict the claim

Always respond in this exact JSON format:
{
  "verdict": "TRUE | FALSE | MISLEADING | UNVERIFIED",
  "credibility_score": 0-100,
  "explanation": "...",
  "supporting_sources": ["url1", "url2"],
  "contradicting_sources": ["url3"]
}
"""


async def fact_check(claim: str) -> dict:
    """
    Main AI agent function:
    1. Scrape sources using Playwright
    2. Feed sources + claim to Gemini
    3. Return structured verdict
    """
    print(f"[Agent] Fact-checking: {claim}")

    # Step 1 — Playwright scrapes the web
    sources = await scrape_sources(claim, max_results=5)
    print(f"[Agent] Found {len(sources)} sources")

    if not sources:
        return {
            "verdict": "UNVERIFIED",
            "credibility_score": 0,
            "explanation": "No sources could be found to verify this claim.",
            "supporting_sources": [],
            "contradicting_sources": [],
            "sources": []
        }

    # Step 2 — Build prompt for Gemini
    sources_text = "\n\n".join([
        f"Source {i+1}:\nTitle: {s['title']}\nURL: {s['url']}\nSnippet: {s['snippet']}"
        for i, s in enumerate(sources)
    ])

    prompt = f"""
{SYSTEM_PROMPT}

CLAIM TO FACT-CHECK:
"{claim}"

SOURCES FOUND:
{sources_text}

Respond with JSON only.
"""

    # Step 3 — Gemini analyses and returns verdict
    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Clean up markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    result = json.loads(raw.strip())
    result["sources"] = sources
    return result
