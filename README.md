# 🕵️ News Fact Checker Agent

An AI-powered backend agent that fact-checks any news headline or claim in real time. Built with **Python, FastAPI, GraphQL, Playwright, Gemini AI, PostgreSQL, and Neo4j**.

## How It Works

1. **You submit a claim** via GraphQL mutation
2. **Playwright** crawls the web and scrapes relevant news sources
3. **Gemini AI Agent** analyses all sources and returns a structured verdict
4. **PostgreSQL** logs every fact-check request and result
5. **Neo4j** stores the knowledge graph of claim → source relationships

```
User → GraphQL Mutation
         ↓
    Playwright scrapes web
         ↓
    Gemini AI analyses sources
         ↓
    Verdict: TRUE / FALSE / MISLEADING / UNVERIFIED
         ↓
    Saved to PostgreSQL (logs) + Neo4j (graph)
```

## Tech Stack

| Technology | Usage |
|---|---|
| **Python** | Core language for entire backend |
| **FastAPI** | REST + GraphQL API server |
| **Strawberry GraphQL** | GraphQL schema, queries and mutations |
| **Playwright** | Headless browser for web scraping |
| **Gemini 1.5 Flash** | AI agent for source analysis and verdict |
| **PostgreSQL + SQLAlchemy** | Stores fact-check history and logs |
| **Neo4j** | Graph DB for claim→source relationships |

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/news-fact-checker.git
cd news-fact-checker
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Add your GEMINI_API_KEY from https://aistudio.google.com
```

### 3. Run with Docker (recommended)
```bash
docker-compose up --build
```

### 4. Or run locally
```bash
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload
```

## Usage

Open **http://localhost:8000/graphql** and run:

### Fact-check a claim
```graphql
mutation {
  factCheckClaim(claim: "Scientists discover water on Mars") {
    verdict
    credibilityScore
    explanation
    supportingSources
    contradictingSources
    sources {
      title
      url
      snippet
    }
  }
}
```

### View fact-check history
```graphql
query {
  history(limit: 10) {
    id
    claim
    verdict
    credibilityScore
    explanation
  }
}
```

### Query the knowledge graph
```graphql
query {
  claimGraph(claim: "Scientists discover water on Mars") {
    verdict
    sources {
      title
      url
      relationship
    }
  }
}
```

## Example Response

```json
{
  "verdict": "MISLEADING",
  "credibility_score": 42,
  "explanation": "While NASA has confirmed evidence of ancient water on Mars, there is no recent discovery of liquid water. The claim oversimplifies existing research.",
  "supporting_sources": ["https://nasa.gov/..."],
  "contradicting_sources": ["https://bbc.com/..."]
}
```

## Project Structure

```
news-fact-checker/
├── app/
│   ├── main.py       # FastAPI app entry point
│   ├── schema.py     # GraphQL schema (Strawberry)
│   ├── agent.py      # Gemini AI agent logic
│   ├── scraper.py    # Playwright web scraper
│   ├── database.py   # PostgreSQL models & queries
│   └── graph_db.py   # Neo4j graph operations
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Author

**Pushkar Raj** — Full Stack Developer | Backend & AI Systems  
[GitHub](https://github.com/yourusername) • [Email](mailto:rpushkar367@gmail.com)