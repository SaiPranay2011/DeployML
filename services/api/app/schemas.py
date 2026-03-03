from pydantic import BaseModel

class ModelCreate(BaseModel):
    name: str
    framework: str

class ModelOut(BaseModel):
    id: str
    name: str
    framework: str

    class Config:
        from_attributes = True

class ModelVersionOut(BaseModel):
    id: str
    model_id: str
    version: int
    artifact_path: str

    class Config:
        from_attributes = True

class DeploymentCreate(BaseModel):
    model_version_id: str

class DeploymentOut(BaseModel):
    id: str
    model_version_id: str
    status: str
    container_name: str | None = None 
    internal_url: str | None = None

    class Config:
        from_attributes = True

class InferRequest(BaseModel):
    inputs: list[list[float]]

class InferResponse(BaseModel):
    predictions: list