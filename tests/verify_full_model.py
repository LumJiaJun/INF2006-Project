import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
COMPARISON_FIELDS = (
    "dataset",
    "train_rows",
    "test_rows",
    "selection_metric",
    "selected_model",
    "evaluations",
)


def parse_args():
    parser = argparse.ArgumentParser(description="Replay and verify the full-data model evaluation.")
    parser.add_argument("--listings", type=Path, required=True)
    parser.add_argument(
        "--expected",
        type=Path,
        default=ROOT / "analytics/artifacts/model_evaluation.json",
    )
    parser.add_argument("--output-directory", type=Path, default=ROOT / "tmp/full-model-verification")
    return parser.parse_args()


def main():
    args = parse_args()
    expected = json.loads(args.expected.read_text(encoding="utf-8"))
    args.output_directory.mkdir(parents=True, exist_ok=True)
    model_path = args.output_directory / "airbnb_price_model.joblib"
    metrics_path = args.output_directory / "model_evaluation.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "analytics/train_model.py"),
            "--listings",
            str(args.listings),
            "--model-output",
            str(model_path),
            "--metrics-output",
            str(metrics_path),
        ],
        cwd=ROOT,
        check=True,
    )
    actual = json.loads(metrics_path.read_text(encoding="utf-8"))
    mismatches = [field for field in COMPARISON_FIELDS if actual[field] != expected[field]]
    for field in ("sha256", "size_bytes"):
        if actual["model_artifact"][field] != expected["model_artifact"][field]:
            mismatches.append(f"model_artifact.{field}")
    if mismatches:
        raise RuntimeError(f"Full-data reproduction differs in: {', '.join(mismatches)}")
    print("Full-data model reproduction matched the committed evaluation exactly.")
    print(f"Compared fields: {', '.join(COMPARISON_FIELDS)}, model SHA-256, model size")


if __name__ == "__main__":
    main()
