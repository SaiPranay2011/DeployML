from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db import get_db
from .. import models
from ..models_logs import InferenceLog

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/deployments/{deployment_id}")
def deployment_metrics(deployment_id: str, db: Session = Depends(get_db)):
    d = db.query(models.Deployment).filter(models.Deployment.id == deployment_id).first()
    if not d:
        raise HTTPException(status_code=404, detail=" Deployment not found")
    
    total = db.query(func.count(InferenceLog.id)).filter(InferenceLog.deployment_id == deployment_id).scalar() or 0
    avg_latency = db.query(func.avg(InferenceLog.latency_ms)).filter(InferenceLog.deployment_id == deployment_id).scalar()
    p95_latency = (
        db.query(InferenceLog.latency_ms)
        .filter(InferenceLog.deployment_id == deployment_id)
        .order_by(InferenceLog.latency_ms.desc())
        .offset(max(int(total * 0.05) - 1, 0))
        .limit(1)
        .scalar()
    )

    errors = db.query(func.count(InferenceLog.id)).filter(
        InferenceLog.deployment_id == deployment_id,
        InferenceLog.status_code != 200
    ).scalar() or 0

    return {
        "deloyment_id": deployment_id,
        "total_requests": total,
        "error_requests": errors,
        "avg_latency_ms": float(avg_latency) if avg_latency is not None else None,
        "p95_latency_ms": float(p95_latency) if p95_latency is not None else None,
    }