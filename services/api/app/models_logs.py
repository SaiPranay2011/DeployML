import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def uuid_str():
    return str(uuid.uuid4())

class InferenceLog(Base):
    __tablename__ = "inference_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=uuid_str)
    deployment_id: Mapped[str] = mapped_column(ForeignKey("deployments.id"), nullable=False)

    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))