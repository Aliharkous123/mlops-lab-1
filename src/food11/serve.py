import os
import io

import mlflow
import torch
from fastapi import FastAPI, UploadFile, File
from PIL import Image
from torchvision import transforms

# Get the MLflow server address from the environment variable.
# If it is not defined, use the local MLflow server.
MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000"
)

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Load the model registered in MLflow with the "champion" alias
model = mlflow.pyfunc.load_model("models:/food11@champion")

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    # Read the uploaded image
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")

    # Apply the same basic preprocessing used by ResNet18
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    image_tensor = transform(image).unsqueeze(0)

    # Run prediction using the MLflow model
    prediction = model.predict(image_tensor.numpy())

    prediction_tensor = torch.tensor(prediction)

    probabilities = torch.softmax(prediction_tensor, dim=1)

    confidence, predicted_class = torch.max(probabilities, 1)

    return {
        "predicted_category": int(predicted_class.item()),
        "confidence": float(confidence.item())
    }