from neo4j import GraphDatabase
import os

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = None


def init_graph():
    """Connect to Neo4j on startup."""
    global driver
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("[Neo4j] Graph database connected ✅")
    except Exception as e:
        print(f"[Neo4j] Connection failed (optional): {e}")
        driver = None


def save_claim_graph(claim: str, verdict: str, sources: list[dict],
                     supporting: list[str], contradicting: list[str]):
    """
    Store the claim and its source relationships in Neo4j.

    Graph structure:
    (:Claim {text, verdict}) -[:SUPPORTED_BY]->  (:Source {url, title})
    (:Claim {text, verdict}) -[:CONTRADICTED_BY]-> (:Source {url, title})
    """
    if not driver:
        return

    with driver.session() as session:
        # Create or merge the Claim node
        session.run(
            """
            MERGE (c:Claim {text: $text})
            SET c.verdict = $verdict
            """,
            text=claim, verdict=verdict
        )

        # Create source nodes and relationships
        for source in sources:
            url   = source.get("url", "")
            title = source.get("title", "")

            if url in supporting:
                rel = "SUPPORTED_BY"
            elif url in contradicting:
                rel = "CONTRADICTED_BY"
            else:
                rel = "REFERENCED_BY"

            session.run(
                f"""
                MERGE (s:Source {{url: $url}})
                SET s.title = $title
                WITH s
                MATCH (c:Claim {{text: $claim}})
                MERGE (c)-[:{rel}]->(s)
                """,
                url=url, title=title, claim=claim
            )


def get_claim_graph(claim: str) -> dict:
    """Fetch a claim and all its related sources from Neo4j."""
    if not driver:
        return {}

    with driver.session() as session:
        result = session.run(
            """
            MATCH (c:Claim {text: $text})-[r]->(s:Source)
            RETURN c.verdict AS verdict, type(r) AS relationship,
                   s.url AS url, s.title AS title
            """,
            text=claim
        )
        rows = result.data()
        return {
            "claim":   claim,
            "verdict": rows[0]["verdict"] if rows else "UNKNOWN",
            "sources": [
                {"url": r["url"], "title": r["title"], "relationship": r["relationship"]}
                for r in rows
            ]
        }
