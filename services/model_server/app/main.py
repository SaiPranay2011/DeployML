import os 
import pickle
from fastapi import FastAPI
from pydantic import BaseModel

MODEL_PATH = os.environ.get("MODEL_PATH")
if not MODEL_PATH:
    raise RuntimeError("MODEL_PATH env var is required")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

app = FastAPI(title="DeployML - Model Server")

class PredictRequest(BaseModel):
    inputs: list[list[float]]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict(req: PredictRequest):
    preds = model.predict(req.inputs).tolist()
    return {"predictions": preds}