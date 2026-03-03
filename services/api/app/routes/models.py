import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db import get_db
from .. import models, schemas
from ..storage.artifacts import save_model_artifact

router = APIRouter(prefix="/models", tags=["models"])

@router.post("", response_model=schemas.ModelOut)
def create_model(payload: schemas.ModelCreate, db: Session = Depends(get_db)):
    m = models.Model(name=payload.name, framework=payload.framework)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

@router.get("", response_model=list[schemas.ModelOut])
def list_models(db: Session = Depends(get_db)):
    return db.query(models.Model).all()

@router.get("/{model_id}/versions", response_model=list[schemas.ModelVersionOut])
def list_versions(model_id: str, db: Session = Depends(get_db)):
    model = db.query(models.Model).filter(models.Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    versions = (
        db.query(models.ModelVersion)
        .filter(models.ModelVersion.model_id == model_id)
        .order_by(models.ModelVersion.version.desc())
        .all()
    )
    return versions

@router.post("/{model_id}/versions", response_model=schemas.ModelVersionOut)
def upload_version(
    model_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1) Validate model exists
    model = db.query(models.Model).filter(models.Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # 2) Validate file type (V1: .pkl only)
    if not file.filename or not file.filename.lower().endswith(".pkl"):
        raise HTTPException(status_code=400, detail="V1 supports only .pkl model files")

    # 3) Determine next version number
    current_max = (
        db.query(func.max(models.ModelVersion.version))
        .filter(models.ModelVersion.model_id == model_id)
        .scalar()
    )
    next_version = 1 if current_max is None else int(current_max) + 1

    # 4) Save artifact to shared volume
    artifacts_dir = os.environ.get("ARTIFACTS_DIR", "/artifacts")
    artifact_path = save_model_artifact(
        artifacts_root=artifacts_dir,
        model_id=model_id,
        version=next_version,
        file=file,
    )

    # 5) Insert DB record
    mv = models.ModelVersion(
        model_id=model_id,
        version=next_version,
        artifact_path=artifact_path,
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)
    return mv