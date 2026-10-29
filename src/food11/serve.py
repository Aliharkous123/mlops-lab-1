import io
import os
from typing import Annotated

import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from torchvision import transforms

import mlflow
from src.food11.data import CLASSES

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000"
)

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

app = FastAPI()

# Model is loaded when the application starts, not during import.
model = None


@app.on_event("startup")
def load_model():
    global model

    if os.environ.get("SKIP_MODEL"):
        return

    model = mlflow.pyfunc.load_model("models:/food11@champion")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: Annotated[UploadFile, File()]):
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded"
        )

    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    image_tensor = transform(image).unsqueeze(0)

    prediction = model.predict(image_tensor.numpy())

    prediction_tensor = torch.tensor(prediction)
    probabilities = torch.softmax(prediction_tensor, dim=1)

    confidence, predicted_class = torch.max(probabilities, 1)

    class_id = int(predicted_class.item())

    return {
        "predicted_category": class_id,
        "category": CLASSES[class_id],
        "confidence": float(confidence.item())
    }