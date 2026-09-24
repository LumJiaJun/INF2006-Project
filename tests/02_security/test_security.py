"""
Test 2 — Security controls.

Objective: prove authentication/authorization enforcement, rejection
of malformed/malicious input, and that passwords are never stored in
plaintext.

Run:
    cd tests
    pytest 02_security -v
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "backend"))
from app.database import SessionLocal
from app import models


def test_unauthenticated_booking_rejected(client):
    r = client.post("/api/bookings", json={
        "listing_id": 1,
        "check_in": "2026-12-01T14:00:00",
        "check_out": "2026-12-04T11:00:00",
        "guests": 2,
    })
    assert r.status_code == 401


def test_invalid_jwt_rejected(client):
    r = client.get("/api/bookings", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_wrong_password_rejected(client):
    client.post("/api/auth/register", json={
        "name": "Sec Test", "email": "sectest@example.com", "password": "CorrectPass123",
    })
    r = client.post("/api/auth/login", json={
        "email": "sectest@example.com", "password": "WrongPassword",
    })
    assert r.status_code == 401


def test_duplicate_registration_rejected(client):
    payload = {"name": "Dup", "email": "dup@example.com", "password": "SomePass123"}
    r1 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/api/auth/register", json=payload)
    assert r2.status_code == 400


def test_malformed_registration_rejected(client):
    r = client.post("/api/auth/register", json={
        "name": "", "email": "not-an-email", "password": "123",
    })
    assert r.status_code == 422


def test_sql_injection_payload_is_not_executed(client):
    r = client.get("/api/listings", params={"city": "Singapore' OR '1'='1"})
    assert r.status_code == 200
    # A vulnerable query would return every row; the parameterized
    # ORM query correctly returns zero matches for the literal string.
    assert r.json()["total"] == 0


def test_password_not_stored_in_plaintext(client):
    plaintext = "SuperSecretPass123"
    client.post("/api/auth/register", json={
        "name": "Hash Check", "email": "hashcheck@example.com", "password": plaintext,
    })
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.email == "hashcheck@example.com").first()
    db.close()
    assert user is not None
    assert user.password_hash != plaintext
    assert user.password_hash.startswith("$2b$")  # bcrypt hash prefix


def test_guest_cannot_cancel_another_users_booking(client):
    # User A books
    client.post("/api/auth/register", json={"name": "A", "email": "usera@example.com", "password": "PassA1234"})
    token_a = client.post("/api/auth/login", json={"email": "usera@example.com", "password": "PassA1234"}).json()["access_token"]
    booking = client.post("/api/bookings", headers={"Authorization": f"Bearer {token_a}"}, json={
        "listing_id": 1, "check_in": "2027-02-01T14:00:00", "check_out": "2027-02-03T11:00:00", "guests": 1,
    }).json()

    # User B tries to cancel A's booking
    client.post("/api/auth/register", json={"name": "B", "email": "userb@example.com", "password": "PassB1234"})
    token_b = client.post("/api/auth/login", json={"email": "userb@example.com", "password": "PassB1234"}).json()["access_token"]
    r = client.patch(f"/api/bookings/{booking['booking_id']}/cancel", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 403


def test_guest_cannot_access_admin_analytics(client, registered_user_token):
    headers = {"Authorization": f"Bearer {registered_user_token}"}
    r = client.get("/api/admin/analytics", headers=headers)
    assert r.status_code == 403


def test_guest_cannot_create_listing_via_admin_endpoint(client, registered_user_token):
    headers = {"Authorization": f"Bearer {registered_user_token}"}
    r = client.post("/api/admin/listings", headers=headers, json={
        "name": "Sneaky listing", "neighbourhood": "Bugis", "city": "Singapore",
        "property_type": "Apartment", "room_type": "Entire home/apt",
        "accommodates": 2, "bedrooms": 1, "price": 100.0,
    })
    assert r.status_code == 403


def test_admin_can_manage_listings(client):
    client.post("/api/auth/register", json={"name": "Admin Test", "email": "admintest@example.com", "password": "AdminPass123"})
    # Promote to admin directly via DB, since registration always creates a guest.
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.email == "admintest@example.com").first()
    user.role = models.UserRole.admin
    db.commit()
    db.close()

    token = client.post("/api/auth/login", json={"email": "admintest@example.com", "password": "AdminPass123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/admin/analytics", headers=headers)
    assert r.status_code == 200
    assert "total_revenue" in r.json()

    r = client.post("/api/admin/listings", headers=headers, json={
        "name": "New Admin Listing", "neighbourhood": "Bugis", "city": "Singapore",
        "property_type": "Apartment", "room_type": "Entire home/apt",
        "accommodates": 2, "bedrooms": 1, "price": 120.0,
    })
    assert r.status_code == 201
    listing_id = r.json()["listing_id"]

    r = client.patch(f"/api/admin/listings/{listing_id}", headers=headers, json={"price": 999.0})
    assert r.status_code == 200
    assert r.json()["price"] == 999.0

    r = client.delete(f"/api/admin/listings/{listing_id}", headers=headers)
    assert r.status_code == 204


def test_guest_cannot_access_admin_bookings_or_pricing_insights(client, registered_user_token):
    headers = {"Authorization": f"Bearer {registered_user_token}"}
    r1 = client.get("/api/admin/bookings", headers=headers)
    assert r1.status_code == 403
    r2 = client.get("/api/admin/pricing-insights", headers=headers)
    assert r2.status_code == 403
    r3 = client.get("/api/admin/listings-pricing", headers=headers)
    assert r3.status_code == 403


def test_guest_cannot_access_admin_users_or_reviews(client, registered_user_token):
    headers = {"Authorization": f"Bearer {registered_user_token}"}
    assert client.get("/api/admin/users", headers=headers).status_code == 403
    assert client.get("/api/admin/reviews", headers=headers).status_code == 403
    assert client.patch("/api/admin/users/1", headers=headers, json={"role": "admin"}).status_code == 403
    assert client.delete("/api/admin/users/1", headers=headers).status_code == 403


def test_admin_can_manage_users_but_not_demote_self(client):
    client.post("/api/auth/register", json={"name": "UserMgmt Admin", "email": "usermgmtadmin@example.com", "password": "AdminPass123"})
    db = SessionLocal()
    admin_user = db.query(models.User).filter(models.User.email == "usermgmtadmin@example.com").first()
    admin_user.role = models.UserRole.admin
    db.commit()
    admin_id = admin_user.user_id
    db.close()
    admin_token = client.post("/api/auth/login", json={"email": "usermgmtadmin@example.com", "password": "AdminPass123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    client.post("/api/auth/register", json={"name": "Plain Guest", "email": "plainguest@example.com", "password": "GuestPass123"})

    r = client.get("/api/admin/users?page_size=50", headers=headers)
    assert r.status_code == 200
    target = next(u for u in r.json() if u["email"] == "plainguest@example.com")

    r = client.patch(f"/api/admin/users/{target['user_id']}", headers=headers, json={"role": "host"})
    assert r.status_code == 200
    assert r.json()["role"] == "host"

    r = client.patch(f"/api/admin/users/{admin_id}", headers=headers, json={"role": "guest"})
    assert r.status_code == 400
