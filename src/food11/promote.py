
import argparse
import math

from mlflow.tracking import MlflowClient

import mlflow

MODEL_NAME = "food11"


def get_accuracy(client, model_version):
    run = client.get_run(model_version.run_id)
    accuracy = run.data.metrics.get("test_accuracy")

    if accuracy is None:
        raise ValueError(
            f"Missing test_accuracy for version {model_version.version}"
        )

    return accuracy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-version", required=True)
    parser.add_argument("--n-test", type=int, required=True)
    args = parser.parse_args()

    if args.n_test <= 0:
        parser.error("--n-test must be positive")

    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    client = MlflowClient()

    champion = client.get_model_version_by_alias(
        MODEL_NAME, "champion"
    )

    candidate = client.get_model_version(
        MODEL_NAME, args.candidate_version
    )

    if candidate.version == champion.version:
        raise ValueError("Candidate cannot be the current champion")

    champion_accuracy = get_accuracy(client, champion)
    candidate_accuracy = get_accuracy(client, candidate)

    standard_error = math.sqrt(
        champion_accuracy * (1 - champion_accuracy) / args.n_test
    )

    threshold = champion_accuracy + 2 * standard_error

    print(f"Champion version: {champion.version}")
    print(f"Candidate version: {candidate.version}")
    print(f"Champion accuracy: {champion_accuracy:.4f}")
    print(f"Candidate accuracy: {candidate_accuracy:.4f}")
    print(f"Standard error: {standard_error:.4f}")
    print(f"Promotion threshold: {threshold:.4f}")

    if candidate_accuracy >= threshold:
        decision = "champion"
        client.set_registered_model_alias(
            MODEL_NAME, "champion", candidate.version
        )
        print("PASS: Candidate promoted to champion")
    else:
        decision = "challenger"
        client.set_registered_model_alias(
            MODEL_NAME, "challenger", candidate.version
        )
        print("FAIL: Candidate assigned challenger alias")

    client.set_model_version_tag(
        MODEL_NAME, candidate.version, "decision", decision
    )
    client.set_model_version_tag(
        MODEL_NAME,
        candidate.version,
        "candidate_accuracy",
        str(candidate_accuracy),
    )
    client.set_model_version_tag(
        MODEL_NAME,
        candidate.version,
        "champion_accuracy",
        str(champion_accuracy),
    )


if __name__ == "__main__":
    main()
