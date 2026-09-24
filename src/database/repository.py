"""Repository methods for analysis history; API code stays database-agnostic."""

import json
from datetime import datetime

from sqlalchemy import func, select

from .models import Analysis
from .session import SessionLocal, initialize_database


class AnalysisRepository:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory
        initialize_database()

    def save(self, result: dict) -> dict:
        record = Analysis(id=result["id"], url=result["url"], created_at=datetime.fromisoformat(result["created_at"]), trust_score=result["trust_score"], risk_level=result["risk_level"], ml_probability=result.get("ml_prediction", {}).get("probability"), model_version=result["model_version"], status=result["status"], result_json=json.dumps(result))
        with self.session_factory() as session:
            session.add(record)
            session.commit()
        return result

    def get(self, analysis_id: str) -> dict | None:
        with self.session_factory() as session:
            record = session.get(Analysis, analysis_id)
            return json.loads(record.result_json) if record else None

    def history(self, limit: int = 50) -> list[dict]:
        with self.session_factory() as session:
            records = session.scalars(select(Analysis).order_by(Analysis.created_at.desc()).limit(min(limit, 100))).all()
            return [json.loads(record.result_json) for record in records]

    def statistics(self) -> dict:
        with self.session_factory() as session:
            total = session.scalar(select(func.count()).select_from(Analysis)) or 0
            average = session.scalar(select(func.avg(Analysis.trust_score)))
            high = session.scalar(select(func.count()).select_from(Analysis).where(Analysis.risk_level == "high_observed_risk")) or 0
            low = session.scalar(select(func.count()).select_from(Analysis).where(Analysis.risk_level == "low_observed_risk")) or 0
            return {"total_analyses": int(total), "average_trust_score": round(float(average), 2) if average is not None else None, "high_risk_analyses": int(high), "low_risk_analyses": int(low)}