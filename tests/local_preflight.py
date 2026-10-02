import argparse
import shutil
import subprocess
import sys
import json
import threading
import urllib.request
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))


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


def smoke_local_website(model_path):
    import joblib

    from src.local_server import create_server

    server = create_server(port=0, model_bundle=joblib.load(model_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(f"{base_url}/", timeout=10) as response:
            if response.status != 200 or b"Airbnb" not in response.read():
                raise RuntimeError("Local frontend smoke check failed.")
        with urllib.request.urlopen(f"{base_url}/api/health", timeout=10) as response:
            if json.load(response)["status"] != "healthy":
                raise RuntimeError("Local health smoke check failed.")
        with urllib.request.urlopen(f"{base_url}/api/analytics", timeout=10) as response:
            if json.load(response)["count"] != 10:
                raise RuntimeError("Local analytics smoke check failed.")
        with urllib.request.urlopen(f"{base_url}/model-options.json", timeout=10) as response:
            options = json.load(response)
        city = options["cities"][0]
        latitude = city["coordinate_range"]["latitude"]
        longitude = city["coordinate_range"]["longitude"]
        payload = {
            "city": city["name"],
            "neighbourhood": city["neighbourhoods"][0],
            "property_type": options["property_types"][0],
            "room_type": options["room_types"][0],
            "instant_bookable": True,
            "host_is_superhost": False,
            "host_identity_verified": True,
            "latitude": (latitude["minimum"] + latitude["maximum"]) / 2,
            "longitude": (longitude["minimum"] + longitude["maximum"]) / 2,
            "accommodates": 2,
            "bedrooms": 1,
            "minimum_nights": 2,
            "review_scores_rating": 90,
            "host_total_listings_count": 1,
            "amenities_count": 8,
        }
        request = urllib.request.Request(
            f"{base_url}/api/predict",
            data=json.dumps(payload).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            prediction = json.load(response)
            if response.status != 200 or prediction["estimated_nightly_price"] <= 0:
                raise RuntimeError("Local prediction smoke check failed.")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    print("Validated local frontend, health, analytics, schema, and prediction routes.")


def main():
    args = parse_args()
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"])
    run([sys.executable, "-m", "compileall", "-q", "analytics", "src", "tests"])
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
        smoke_local_website(output / "sample-model.joblib")

    print("\nLocal preflight completed successfully.")


if __name__ == "__main__":
    main()
