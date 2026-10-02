import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def parse_args():
    parser = argparse.ArgumentParser(description="Run safe local submission checks.")
    parser.add_argument("--include-ml", action="store_true", help="Train and evaluate against synthetic sample data.")
    return parser.parse_args()


def run(command, cwd=ROOT):
    print(f"\n> {' '.join(str(part) for part in command)}")
    subprocess.run(command, cwd=cwd, check=True)


def validate_manifest_paths():
    manifest = yaml.safe_load((ROOT / "project_manifest.yaml").read_text(encoding="utf-8"))
    paths = [
        manifest["architecture"]["diagram"],
        manifest["architecture"]["review"],
        *manifest["evidence"].values(),
        manifest["data_ai"]["dataset"],
        manifest["data_ai"]["cloud_pipeline_evidence"],
        manifest["security"]["threat_control_map"],
        manifest["declarations"]["ai_use"],
        manifest["declarations"]["contributions"],
    ]
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise FileNotFoundError(f"Manifest paths do not exist: {missing}")
    print(f"Validated {len(paths)} manifest paths.")


def main():
    args = parse_args()
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"])
    run([sys.executable, "-m", "compileall", "-q", "analytics", "src/backend", "tests"])
    validate_manifest_paths()

    node = shutil.which("node")
    if node:
        for path in sorted((ROOT / "src" / "frontend").glob("*.js")):
            run([node, "--check", str(path)])
    else:
        print("Node.js is unavailable; frontend syntax checks were skipped.")

    terraform = shutil.which("terraform")
    if terraform:
        run([terraform, "fmt", "-check", "-recursive"], ROOT / "src" / "infrastructure")
        if (ROOT / "src" / "infrastructure" / ".terraform").is_dir():
            run([terraform, "validate"], ROOT / "src" / "infrastructure")
        else:
            print("Terraform providers are not initialized; run terraform init -backend=false before validate.")
    else:
        print("Terraform is unavailable; formatting and validation checks were skipped.")

    if args.include_ml:
        output = ROOT / "tmp" / "local-preflight"
        run(
            [
                sys.executable,
                "analytics/train_model.py",
                "--listings",
                "data/sample/listings_synthetic.csv",
                "--model-output",
                str(output / "sample-model.joblib"),
                "--metrics-output",
                str(output / "sample-metrics.json"),
            ]
        )

    print("\nLocal preflight completed successfully.")


if __name__ == "__main__":
    main()
