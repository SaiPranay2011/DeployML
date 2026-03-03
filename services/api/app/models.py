import uuid
from datetime import datetime, timezone
from sqlalchemy import String,DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped,mapped_column, relationship
from .db import Base
def uuid_str():
    return str(uuid.uuid4())

class Model(Base):
    __tablename__= "models"
    id: Mapped[str] = mapped_column(String,primary_key=True,default=uuid_str)
    name: Mapped[str] = mapped_column(String,nullable=False)
    framework: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))

    versions: Mapped[list["ModelVersion"]] = relationship(back_populates="model")

class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[str] = mapped_column(String,primary_key=True, default=uuid_str)
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    artifact_path: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))

    model: Mapped["Model"] = relationship(back_populates="versions")
    deployments: Mapped[list["Deployment"]] = relationship(back_populates="model_version")

class Deployment(Base):
    __tablename__ = "deployments"
    id: Mapped[str] = mapped_column(String,primary_key=True, default=uuid_str)
    model_version_id: Mapped[str] = mapped_column(ForeignKey("model_versions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String,nullable=False, default="Deploying")
    container_name: Mapped[str] = mapped_column(String,nullable=True)
    internal_url: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc))

    model_version: Mapped["ModelVersion"] = relationship(back_populates="deployments")