from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from .. import models, schemas
from ..deployer.docker_deployer import DockerDeployer

router = APIRouter(prefix="/deployments", tags=["deployments"])

@router.get("", response_model=list[schemas.DeploymentOut])
def list_deployments(db: Session = Depends(get_db)):
    return db.query(models.Deployment).order_by(models.Deployment.created_at.desc()).all()

@router.get("/{deployment_id}", response_model=schemas.DeploymentOut)
def get_deployment(deployment_id: str, db: Session = Depends(get_db)):
    d = db.query(models.Deployment).filter(models.Deployment.id == deployment_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return d

@router.post("", response_model=schemas.DeploymentOut)
def create_deployment(payload: schemas.DeploymentCreate, db: Session = Depends(get_db)):
    # 1) Validate model_version exists
    mv = (
        db.query(models.ModelVersion)
        .filter(models.ModelVersion.id == payload.model_version_id)
        .first()
    )
    if not mv:
        raise HTTPException(status_code=404, detail="Model version not found")

    # 2) Create deployment record
    d = models.Deployment(
        model_version_id=mv.id,
        status="DEPLOYING",
        container_name=None,
        internal_url=None,
    )
    db.add(d)
    db.commit()
    db.refresh(d)

    deployer = DockerDeployer()

    # 3) Start container
    container_name, internal_url = deployer.start_model_server(
        deployment_id=d.id,
        model_path=mv.artifact_path,   # e.g. /artifacts/<model_id>/v1/model.pkl
    )

    # 4) Health check
    ok = deployer.wait_for_health(internal_url, timeout_seconds=25)

    if ok:
        d.status = "RUNNING"
        d.container_name = container_name
        d.internal_url = internal_url
        db.commit()
        db.refresh(d)
        return d

    # FAILED path: clean up container
    deployer.stop_and_remove(container_name)
    d.status = "FAILED"
    d.container_name = container_name
    d.internal_url = internal_url
    db.commit()
    db.refresh(d)
    return d

@router.delete("/{deployment_id}", response_model=schemas.DeploymentOut)
def stop_deployment(deployment_id: str, db: Session = Depends(get_db)):
    d = db.query(models.Deployment).filter(models.Deployment.id == deployment_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if not d.container_name:
        d.status = "STOPPED"
        db.commit()
        db.refresh(d)
        return d
    deployer = DockerDeployer()
    deployer.stop_and_remove(d.container_name)

    d.status = "STOPPED"
    db.commit()
    db.refresh(d)
    return d

@router.get("/{deployment_id}/logs")
def get_deployment_logs(deployment_id: str, db: Session = Depends(get_db)):
    d = db.query(models.Deployment).filter(models.Deployment.id == deployment_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if not d.container_name:
        raise HTTPException(status_code=400, detail="Deployment has no container_name")
    deployer = DockerDeployer()
    try:
        c = deployer.client.containers.get(d.container_name)
        logs = c.logs(tail=200).decode("utf-8", errors="replace")
        return {"deployment_id": d.id,"container_name": d.container_name, "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not fetch logs: {str(e)}")