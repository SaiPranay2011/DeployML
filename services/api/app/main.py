from fastapi import FastAPI
from contextlib import asynccontextmanager
from .db import engine
from .models import Base
from .models_logs import InferenceLog

from .routes import models as models_route
from .routes import deployments as deployments_route
from .routes import infer as infer_route
from .routes import metrics as metrics_route

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title='DeployML - Control Plane', lifespan=lifespan)

app.include_router(models_route.router)
app.include_router(deployments_route.router)
app.include_router(infer_route.router)
app.include_router(metrics_route.router)

@app.get("/health")
def health():
    return {"status": "ok"}
