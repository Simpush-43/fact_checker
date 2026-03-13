import strawberry
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
        # 1. Run AI agent (Playwright + Gemini)
        result = await fact_check(claim)

        # 2. Save to PostgreSQL
        await save_fact_check(claim, result)

        # 3. Save relationships to Neo4j
        save_claim_graph(
            claim=claim,
            verdict=result["verdict"],
            sources=result.get("sources", []),
            supporting=result.get("supporting_sources", []),
            contradicting=result.get("contradicting_sources", [])
        )

        return FactCheckResult(
            claim=claim,
            verdict=result["verdict"],
            credibility_score=result["credibility_score"],
            explanation=result["explanation"],
            supporting_sources=result.get("supporting_sources", []),
            contradicting_sources=result.get("contradicting_sources", []),
            sources=[
                SourceType(title=s["title"], url=s["url"], snippet=s.get("snippet", ""))
                for s in result.get("sources", [])
            ]
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
