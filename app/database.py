from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:password@localhost:5432/factchecker"
)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class FactCheckLog(Base):
    __tablename__ = "fact_check_logs"

    id                = Column(Integer, primary_key=True, index=True)
    claim             = Column(Text, nullable=False)
    verdict           = Column(String(20), nullable=False)
    credibility_score = Column(Float, nullable=False)
    explanation       = Column(Text)
    sources_count     = Column(Integer, default=0)
    created_at        = Column(DateTime, default=datetime.utcnow)


async def init_db():
    Base.metadata.create_all(bind=engine)
    print("[DB] PostgreSQL tables ready ✅")


async def save_fact_check(claim: str, result: dict) -> FactCheckLog:
    with SessionLocal() as session:
        log = FactCheckLog(
            claim=claim,
            verdict=result["verdict"],
            credibility_score=result["credibility_score"],
            explanation=result["explanation"],
            sources_count=len(result.get("sources", []))
        )
        session.add(log)
        session.commit()
        session.refresh(log)
        return log


async def get_all_logs(limit: int = 20) -> list:
    with SessionLocal() as session:
        return session.query(FactCheckLog)\
            .order_by(FactCheckLog.created_at.desc())\
            .limit(limit).all()