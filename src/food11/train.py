import argparse
from pathlib import Path

import mlflow
import mlflow.pytorch
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        choices=["processed", "mini"],
        default="mini"
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=5
    )

    parser.add_argument(
        "--lr",
        type=float,
        default=0.001
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32
    )

    return parser.parse_args()


def evaluate(model, loader, criterion, device):
    model.eval()

    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():

        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(outputs, labels)

            total_loss += loss.item() * images.size(0)

            predictions = outputs.argmax(dim=1)

            correct += (predictions == labels).sum().item()
            total += labels.size(0)

    loss = total_loss / total
    accuracy = correct / total

    return loss, accuracy


def main():

    args = get_args()

    # Connect to the local MLflow tracking server
    mlflow.set_tracking_uri("http://127.0.0.1:5000")

    # Use the food11 experiment
    mlflow.set_experiment("food11")

    # Select the dataset
    if args.dataset == "mini":
        data_dir = Path("data/food11_processed_mini")
    else:
        data_dir = Path("data/food11_processed")

    # Image transformations
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])

    # Load datasets
    train_dataset = datasets.ImageFolder(
        data_dir / "training",
        transform=transform
    )

    val_dataset = datasets.ImageFolder(
        data_dir / "validation",
        transform=transform
    )

    test_dataset = datasets.ImageFolder(
        data_dir / "evaluation",
        transform=transform
    )

    # Create DataLoaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False
    )

    # Use GPU if available, otherwise CPU
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Using device:", device)

    # Load pretrained ResNet18
    model = models.resnet18(
        weights=models.ResNet18_Weights.DEFAULT
    )

    # Replace the final layer so the model outputs 11 classes
    number_of_features = model.fc.in_features

    model.fc = nn.Linear(
        number_of_features,
        11
    )

    model = model.to(device)

    # Loss function
    criterion = nn.CrossEntropyLoss()

    # Optimizer
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=args.lr
    )

    # Start MLflow run
    with mlflow.start_run():

        # Log hyperparameters once at the beginning
        mlflow.log_params({
            "dataset": args.dataset,
            "epochs": args.epochs,
            "lr": args.lr,
            "batch_size": args.batch_size,
            "model": "resnet18",
        })

        # Training loop
        for epoch in range(args.epochs):

            model.train()

            total_train_loss = 0.0
            total_train_samples = 0

            for images, labels in train_loader:

                images = images.to(device)
                labels = labels.to(device)

                # Clear previous gradients
                optimizer.zero_grad()

                # Forward pass
                outputs = model(images)

                # Calculate loss
                loss = criterion(
                    outputs,
                    labels
                )

                # Backpropagation
                loss.backward()

                # Update model parameters
                optimizer.step()

                total_train_loss += (
                    loss.item() * images.size(0)
                )

                total_train_samples += images.size(0)

            train_loss = (
                total_train_loss /
                total_train_samples
            )

            # Evaluate on validation data
            val_loss, val_accuracy = evaluate(
                model,
                val_loader,
                criterion,
                device
            )

            # Log metrics at the end of each epoch
            mlflow.log_metric(
                "train_loss",
                train_loss,
                step=epoch
            )

            mlflow.log_metric(
                "val_loss",
                val_loss,
                step=epoch
            )

            mlflow.log_metric(
                "val_accuracy",
                val_accuracy,
                step=epoch
            )

            print(
                f"Epoch {epoch + 1}/{args.epochs} - "
                f"train_loss: {train_loss:.4f} - "
                f"val_loss: {val_loss:.4f} - "
                f"val_accuracy: {val_accuracy:.4f}"
            )

        # Final evaluation on test data
        _, test_accuracy = evaluate(
            model,
            test_loader,
            criterion,
            device
        )

        # Log final test accuracy
        mlflow.log_metric(
            "test_accuracy",
            test_accuracy
        )

        # Log the trained model
        # Pickle is used here because MLflow's default pt2
        # serialization caused an error with this setup
        mlflow.pytorch.log_model(
            model,
            name="model",
            serialization_format="pickle"
        )

        print(
            f"Test accuracy: {test_accuracy:.4f}"
        )


if __name__ == "__main__":
    main()