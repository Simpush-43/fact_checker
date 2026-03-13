import strawberry
import traceback  # <-- Added traceback import
from typing import List, Optional
from app.agent import fact_check
from app.database import save_fact_check, get_all_logs
from app.graph_db import save_claim_graph, get_claim_graph


# ── Types ──────────────────────────────────────────

@strawberry.type
class SourceType:
    title:        str
    url:          str
    snippet:      Optional[str] = ""
    relationship: Optional[str] = ""


@strawberry.type
class FactCheckResult:
    claim:              str
    verdict:            str
    credibility_score:  float
    explanation:        str
    supporting_sources: List[str]
    contradicting_sources: List[str]
    sources:            List[SourceType]


@strawberry.type
class HistoryItem:
    id:               int
    claim:            str
    verdict:          str
    credibility_score: float
    explanation:      str
    sources_count:    int


@strawberry.type
class GraphResult:
    claim:   str
    verdict: str
    sources: List[SourceType]


# ── Queries ────────────────────────────────────────

@strawberry.type
class Query:

    @strawberry.field(description="Get past fact-check history from PostgreSQL")
    async def history(self, limit: int = 10) -> List[HistoryItem]:
        logs = await get_all_logs(limit)
        return [
            HistoryItem(
                id=log.id,
                claim=log.claim,
                verdict=log.verdict,
                credibility_score=log.credibility_score,
                explanation=log.explanation,
                sources_count=log.sources_count
            )
            for log in logs
        ]

    @strawberry.field(description="Get the knowledge graph for a claim from Neo4j")
    def claim_graph(self, claim: str) -> GraphResult:
        data = get_claim_graph(claim)
        return GraphResult(
            claim=data.get("claim", claim),
            verdict=data.get("verdict", "UNKNOWN"),
            sources=[
                SourceType(
                    title=s["title"],
                    url=s["url"],
                    relationship=s["relationship"]
                )
                for s in data.get("sources", [])
            ]
        )


# ── Mutations ──────────────────────────────────────

@strawberry.type
class Mutation:

    @strawberry.mutation(description="Submit a claim to be fact-checked by the AI agent")
    async def fact_check_claim(self, claim: str) -> FactCheckResult:
        try:
            print(f"\n🚀 --- STARTING PIPELINE FOR: {claim} ---")
            
            # 1. Run AI agent (Playwright + Gemini)
            result = await fact_check(claim)
            print("✅ --- AGENT FINISHED, SAVING TO POSTGRES ---")

            # 2. Save to PostgreSQL
            await save_fact_check(claim, result)
            print("✅ --- POSTGRES SAVED, SAVING TO NEO4J ---")

            # 3. Save relationships to Neo4j
            save_claim_graph(
                claim=claim,
                verdict=result.get("verdict", "UNVERIFIED"),
                sources=result.get("sources", []),
                supporting=result.get("supporting_sources", []),
                contradicting=result.get("contradicting_sources", [])
            )
            print("✅ --- NEO4J SAVED, FORMATTING RESULT ---")

            return FactCheckResult(
                claim=claim,
                verdict=result.get("verdict", "UNVERIFIED"),
                credibility_score=result.get("credibility_score", 0.0),
                explanation=result.get("explanation", "No explanation provided."),
                supporting_sources=result.get("supporting_sources", []),
                contradicting_sources=result.get("contradicting_sources", []),
                sources=[
                    SourceType(
                        title=s.get("title", "Unknown Title"), 
                        url=s.get("url", ""), 
                        snippet=s.get("snippet", "")
                    )
                    for s in result.get("sources", [])
                ]
            )

        except Exception as e:
            # THIS forces the exact error to print in the Uvicorn terminal
            print("\n🚨 CRASH IN SCHEMA.PY RESOLVER 🚨")
            traceback.print_exc()
            raise e


schema = strawberry.Schema(query=Query, mutation=Mutation)