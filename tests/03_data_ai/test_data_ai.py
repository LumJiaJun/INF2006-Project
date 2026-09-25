"""
Test 3 — Data / AI validation.

Objective: prove the trained price model exists, was evaluated with a
held-out test set, and the /api/ml/price-estimate endpoint returns an
interpretable estimate using it.

Prerequisite: analytics/train_price_model.py must have been run at
least once (see analytics/README.md).

Run:
    cd tests
    pytest 03_data_ai -v
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "backend"))
from app.database import SessionLocal
from app import models

FIGURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "analytics", "figures")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "src", "backend", "app", "ml_model", "price_model.joblib")


def test_model_artifact_exists():
    assert os.path.exists(MODEL_PATH), "Run analytics/train_price_model.py first"


def test_metrics_file_has_required_fields():
    metrics_path = os.path.join(FIGURES_DIR, "metrics.json")
    assert os.path.exists(metrics_path), "Run analytics/train_price_model.py first"
    with open(metrics_path) as f:
        metrics = json.load(f)
    assert "baseline_linear_regression" in metrics
    assert "random_forest" in metrics
    for key in ("mae", "rmse", "r2"):
        assert key in metrics["baseline_linear_regression"]
        assert key in metrics["random_forest"]
    assert metrics["n_test"] > 0


def test_figures_generated():
    for fname in ("actual_vs_predicted.png", "residuals.png"):
        assert os.path.exists(os.path.join(FIGURES_DIR, fname)), f"Missing {fname}"


def test_price_estimate_endpoint_returns_interpretable_output(client):
    r = client.post("/api/ml/price-estimate", json={
        "city": "Singapore",
        "property_type": "Apartment",
        "room_type": "Entire home/apt",
        "accommodates": 4,
        "bedrooms": 2,
        "minimum_nights": 2,
        "review_scores_rating": 4.5,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["estimated_price"] > 0
    assert body["range_low"] <= body["estimated_price"] <= body["range_high"]
    assert len(body["key_factors"]) > 0
    assert "academic estimate" in body["disclaimer"].lower()


def test_price_estimate_rejects_invalid_input(client):
    r = client.post("/api/ml/price-estimate", json={
        "city": "Singapore",
        "property_type": "Apartment",
        "room_type": "Entire home/apt",
        "accommodates": -1,  # invalid
        "bedrooms": 2,
        "minimum_nights": 2,
    })
    assert r.status_code == 422


def test_booking_made_by_guest_is_visible_to_admin(client):
    """
    Proves a real end-to-end claim: a booking a guest makes is written
    to the shared database and is visible from the admin side, not
    just in the guest's own session.
    """
    client.post("/api/auth/register", json={"name": "Visible Guest", "email": "visibleguest@example.com", "password": "GuestPass123"})
    guest_token = client.post("/api/auth/login", json={"email": "visibleguest@example.com", "password": "GuestPass123"}).json()["access_token"]

    booking = client.post("/api/bookings", headers={"Authorization": f"Bearer {guest_token}"}, json={
        "listing_id": 1, "check_in": "2027-03-01T14:00:00", "check_out": "2027-03-04T11:00:00", "guests": 1,
    }).json()

    client.post("/api/auth/register", json={"name": "Visibility Admin", "email": "visibilityadmin@example.com", "password": "AdminPass123"})
    db = SessionLocal()
    admin_user = db.query(models.User).filter(models.User.email == "visibilityadmin@example.com").first()
    admin_user.role = models.UserRole.admin
    db.commit()
    db.close()
    admin_token = client.post("/api/auth/login", json={"email": "visibilityadmin@example.com", "password": "AdminPass123"}).json()["access_token"]

    r = client.get("/api/admin/bookings", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    booking_ids = [b["booking_id"] for b in r.json()]
    assert booking["booking_id"] in booking_ids
