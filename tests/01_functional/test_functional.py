"""
Test 1 — Functional workflow.

Objective: prove the core guest workflow works end to end —
register -> login -> search -> view listing -> book -> appears in My Trips.
Also covers the budget/requirement-based recommendation feature.

Run:
    cd tests
    pytest 01_functional -v
"""


def test_register_login_search_book_workflow(client):
    # Register
    r = client.post("/api/auth/register", json={
        "name": "Flow Guest", "email": "flow@example.com", "password": "StrongPass123",
    })
    assert r.status_code == 201, r.text
    assert r.json()["email"] == "flow@example.com"

    # Login
    r = client.post("/api/auth/login", json={
        "email": "flow@example.com", "password": "StrongPass123",
    })
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Search
    r = client.get("/api/listings", params={"city": "Singapore"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    listing_id = body["results"][0]["listing_id"]

    # View listing detail
    r = client.get(f"/api/listings/{listing_id}")
    assert r.status_code == 200
    assert r.json()["listing_id"] == listing_id

    # Book
    r = client.post("/api/bookings", headers=headers, json={
        "listing_id": listing_id,
        "check_in": "2026-12-01T14:00:00",
        "check_out": "2026-12-04T11:00:00",
        "guests": 2,
    })
    assert r.status_code == 201, r.text
    booking = r.json()
    assert booking["status"] == "confirmed"
    assert booking["nights"] == 3  # Dec 1 -> Dec 4 = 3 calendar nights

    # My Trips shows it
    r = client.get("/api/bookings", headers=headers)
    assert r.status_code == 200
    booking_ids = [b["booking_id"] for b in r.json()]
    assert booking["booking_id"] in booking_ids


def test_booking_rejects_invalid_dates(client, registered_user_token):
    headers = {"Authorization": f"Bearer {registered_user_token}"}
    r = client.post("/api/bookings", headers=headers, json={
        "listing_id": 1,
        "check_in": "2026-12-10T14:00:00",
        "check_out": "2026-12-09T11:00:00",  # before check_in
        "guests": 2,
    })
    assert r.status_code == 422


def test_double_booking_is_rejected(client, registered_user_token):
    headers = {"Authorization": f"Bearer {registered_user_token}"}
    payload = {
        "listing_id": 1,
        "check_in": "2027-01-01T14:00:00",
        "check_out": "2027-01-05T11:00:00",
        "guests": 2,
    }
    r1 = client.post("/api/bookings", headers=headers, json=payload)
    assert r1.status_code == 201

    overlapping = dict(payload, check_in="2027-01-03T14:00:00", check_out="2027-01-06T11:00:00")
    r2 = client.post("/api/bookings", headers=headers, json=overlapping)
    assert r2.status_code == 409


def test_recommendations_respect_budget_and_capacity(client):
    r = client.post("/api/recommendations", json={
        "budget_min": 50, "budget_max": 300, "guests": 4, "city": "Singapore",
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert "results" in body
    for rec in body["results"]:
        assert rec["accommodates"] >= 4
        assert "fair_price_estimate" in rec
        assert "match_reason" in rec
        assert isinstance(rec["is_great_value"], bool)


def test_recommendations_rejects_invalid_budget_range(client):
    r = client.post("/api/recommendations", json={
        "budget_min": 500, "budget_max": 100, "guests": 2,
    })
    assert r.status_code == 422


def test_availability_endpoint_reflects_existing_booking(client, registered_user_token):
    headers = {"Authorization": f"Bearer {registered_user_token}"}
    booking = client.post("/api/bookings", headers=headers, json={
        "listing_id": 1, "check_in": "2027-04-01T14:00:00", "check_out": "2027-04-05T11:00:00", "guests": 1,
    }).json()

    r = client.get("/api/listings/1/availability")
    assert r.status_code == 200
    ranges = r.json()["booked_ranges"]
    assert any(rg["check_in"].startswith("2027-04-01") for rg in ranges)


def test_chatbot_asks_for_missing_slots_then_returns_recommendations(client):
    r1 = client.post("/api/chatbot/message", json={"message": "I want a place in Singapore for 2 guests"})
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["ready"] is False
    assert body1["state"]["city"] == "Singapore"
    assert body1["state"]["guests"] == 2

    r2 = client.post("/api/chatbot/message", json={"message": "under 200 dollars", "state": body1["state"]})
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["ready"] is True
    assert body2["state"]["budget_max"] == 200
    assert len(body2["recommendations"]) > 0


def test_chatbot_reset_clears_state(client):
    r = client.post("/api/chatbot/message", json={
        "message": "start over",
        "state": {"budget_max": 200, "guests": 2, "city": "Singapore", "budget_min": None, "room_type": None},
    })
    assert r.status_code == 200
    assert r.json()["state"]["city"] is None


def test_guest_can_review_past_booking_and_it_appears_publicly(client, registered_user_token):
    headers = {"Authorization": f"Bearer {registered_user_token}"}
    # Listing 1 in the test fixture has minimum_nights=1, so a short past stay is fine.
    booking = client.post("/api/bookings", headers=headers, json={
        "listing_id": 1, "check_in": "2025-01-01T14:00:00", "check_out": "2025-01-03T11:00:00", "guests": 1,
    }).json()

    r = client.post("/api/reviews", headers=headers, json={
        "booking_id": booking["booking_id"], "rating": 5, "comment": "Loved it",
    })
    assert r.status_code == 201, r.text

    r2 = client.get("/api/listings/1/reviews")
    assert r2.status_code == 200
    assert any(rv["booking_id"] == booking["booking_id"] for rv in r2.json())


def test_guest_cannot_review_future_booking(client, registered_user_token):
    headers = {"Authorization": f"Bearer {registered_user_token}"}
    booking = client.post("/api/bookings", headers=headers, json={
        "listing_id": 1, "check_in": "2027-08-01T14:00:00", "check_out": "2027-08-03T11:00:00", "guests": 1,
    }).json()
    r = client.post("/api/reviews", headers=headers, json={
        "booking_id": booking["booking_id"], "rating": 5, "comment": "too soon",
    })
    assert r.status_code == 400
