from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from app.schema import schema
from app.database import init_db
from app.graph_db import init_graph
from dotenv import load_dotenv
load_dotenv()
app = FastAPI(
    title="News Fact Checker Agent",
    description="AI agent that fact-checks news headlines using Playwright, Gemini, Neo4j & PostgreSQL",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    await init_db()
    init_graph()

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

@app.get("/")
def root():
    return {
        "message": "News Fact Checker Agent is running 🕵️",
        "graphql": "/graphql",
        "docs": "/docs"
    }
