import requests
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas
from ..models_logs import InferenceLog

router = APIRouter(prefix="/infer", tags=["infer"])

@router.post("/{deployment_id}", response_model=schemas.InferResponse)
def infer(deployment_id: str, payload: schemas.InferRequest, db: Session = Depends(get_db)):
    d = db.query(models.Deployment).filter(models.Deployment.id == deployment_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if d.status != "RUNNING" or not d.internal_url:
        raise HTTPException(status_code=400, detail=f"Deployment not Running (status = {d.status})")
    
    start = time.perf_counter()
    status_code = 500
    try:
        r = requests.post(
            f"{d.internal_url}/predict",
            json=payload.model_dump(),
            timeout=10,
        )
        status_code = r.status_code
    except requests.RequestException as e:
        latency_ms = (time.perf_counter() - start) * 1000

        db.add(InferenceLog(deployment_id=d.id, status_code=502, latency_ms=latency_ms))
        db.commit()

        raise HTTPException(status_code=502, detail=f"Model server not reachable: {str(e)}")

    latency_ms = (time.perf_counter() - start) * 1000
    db.add(InferenceLog(deployment_id=d.id, status_code=status_code, latency_ms=latency_ms))
    db.commit()

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Model server error: {r.status_code} {r.text}")
    data = r.json()
    if "predictions" not in data:
        raise HTTPException(status_code=502, detail="Model server response missing 'predictions'")
    return schemas.InferResponse(predictions=data["predictions"])