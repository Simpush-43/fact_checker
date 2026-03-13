from google import genai
import os
import json
from app.scraper import scrape_sources
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are a professional fact-checking AI agent.
Analyze the given claim using your own knowledge.
Determine if the claim is TRUE, FALSE, MISLEADING, or UNVERIFIED.
Give a credibility score from 0 to 100 (100 = definitely true).
Write a short explanation (2-3 sentences).

Always respond in this exact JSON format with no extra text:
{
  "verdict": "TRUE",
  "credibility_score": 85,
  "explanation": "...",
  "supporting_sources": [],
  "contradicting_sources": []
}
"""

async def fact_check(claim: str) -> dict:
    print(f"[Agent] Fact-checking: {claim}", flush=True)

    # Try scraping but don't block if it fails
    sources = await scrape_sources(claim, max_results=5)
    print(f"[Agent] Found {len(sources)} sources", flush=True)

    sources_text = ""
    if sources:
        sources_text = "\n\n".join([
            f"Source {i+1}:\nTitle: {s['title']}\nURL: {s['url']}\nSnippet: {s['snippet']}"
            for i, s in enumerate(sources)
        ])

    prompt = f"""{SYSTEM_PROMPT}

CLAIM TO FACT-CHECK: "{claim}"

{"SOURCES FOUND:" + sources_text if sources_text else "No web sources available — use your own knowledge."}

Respond with JSON only."""

    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=prompt
        )

        raw = (response.text or "").strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        result = json.loads(raw.strip())
        result["sources"] = sources
        return result

    except json.JSONDecodeError:
        return {
            "verdict": "UNVERIFIED",
            "credibility_score": 0,
            "explanation": "AI failed to format response correctly.",
            "supporting_sources": [],
            "contradicting_sources": [],
            "sources": sources
        }
    except Exception as e:
        print(f"[Agent] Error: {e}", flush=True)
        raise e