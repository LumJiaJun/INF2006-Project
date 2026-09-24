"""
Shared fixtures. Points the app at a throwaway SQLite file so tests
never touch the developer's staysphere.db, and seeds it with a couple
of known listings.
"""
import os
import sys
import tempfile

TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "staysphere_test.db")
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["JWT_SECRET"] = "test-secret-do-not-use-in-prod"

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, engine, SessionLocal
from app import models


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(models.Listing(
        listing_id=1, name="Test Loft", host_id=1, host_since="2020-01-01",
        host_location="Singapore", host_response_time="within an hour",
        host_response_rate=90, host_acceptance_rate=90, host_is_superhost=True,
        host_total_listings_count=3, host_has_profile_pic=True, host_identity_verified=True,
        neighbourhood="Bugis", district="Central", city="Singapore",
        latitude=1.3, longitude=103.8, property_type="Loft", room_type="Entire home/apt",
        accommodates=4, bedrooms=2, amenities="Wifi|Kitchen", price=200.0,
        minimum_nights=1, maximum_nights=30, review_scores_rating=4.8,
        review_scores_accuracy=4.8, review_scores_cleanliness=4.8, review_scores_checkin=4.8,
        review_scores_communication=4.8, review_scores_location=4.8, review_scores_value=4.8,
        instant_bookable=True,
    ))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def registered_user_token(client):
    client.post("/api/auth/register", json={
        "name": "Pytest Guest", "email": "pytest@example.com", "password": "StrongPass123",
    })
    resp = client.post("/api/auth/login", json={
        "email": "pytest@example.com", "password": "StrongPass123",
    })
    return resp.json()["access_token"]
