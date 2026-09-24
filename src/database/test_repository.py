import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base
from .repository import AnalysisRepository


class RepositoryTests(unittest.TestCase):
    def test_analysis_survives_new_repository_instance(self):
        with tempfile.TemporaryDirectory() as temporary:
            database_path = Path(temporary) / "history.db"
            engine = create_engine(f"sqlite:///{database_path}", connect_args={"check_same_thread": False})
            Base.metadata.create_all(engine)
            sessions = sessionmaker(bind=engine, expire_on_commit=False)
            result = {"id": "persisted-id", "url": "https://example.com", "created_at": datetime.now(timezone.utc).isoformat(), "trust_score": 72, "risk_level": "moderate_observed_risk", "model_version": "prototype-v2", "status": "complete", "ml_prediction": {"probability": None}, "features": {"security": {}}, "explanation": {}}
            AnalysisRepository(sessions).save(result)
            restarted_store = AnalysisRepository(sessions)
            self.assertEqual(restarted_store.get("persisted-id")["url"], "https://example.com")
            self.assertEqual(restarted_store.statistics()["total_analyses"], 1)
            engine.dispose()


if __name__ == "__main__":
    unittest.main()