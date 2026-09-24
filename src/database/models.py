"""SQLAlchemy persistence models shared by local and production databases."""

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    trust_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ml_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)