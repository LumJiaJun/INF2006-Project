"""
A conversational interface over the SAME recommendation engine used by
POST /api/recommendations (see routers/recommendations.py). This is a
deliberate design choice for an academic project:

- It is NOT a call to an external LLM API (no API key, no per-message
  cost, nothing that could leak data to a third party, fully testable
  offline).
- It IS a real, working conversational UI: it extracts structured
  information (budget, guest count, city, room type) from free-text
  messages using regex/keyword rules, keeps that state across turns so
  the user can change their mind mid-conversation ("actually make it
  $300"), and once enough is known, calls the exact same trained
  price model + ranking heuristic used everywhere else in the app.

This keeps the project's ONE evaluated AI/ML feature (the regression
model + the ranking heuristic built on it) as the single source of
truth, with the chatbot as an additional interface onto it — not a
second, unevaluated "AI" bolted on for its own sake.
"""
import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .recommendations import generate_recommendations

router = APIRouter(prefix="/api", tags=["chatbot"])

RESET_PHRASES = ["start over", "reset", "start again", "new search"]


def known_cities(db: Session) -> list[str]:
    return [c for (c,) in db.query(models.Listing.city).distinct().all()]


def known_room_types(db: Session) -> list[str]:
    return [r for (r,) in db.query(models.Listing.room_type).distinct().all()]


def extract_slots(message: str, cities: list[str], room_types: list[str]) -> dict:
    text = message.lower()
    updates: dict = {}

    for c in cities:
        if c.lower() in text:
            updates["city"] = c
            break

    if any(k in text for k in ("entire home", "entire place", "whole place", "whole home", "entire apartment")):
        match = next((rt for rt in room_types if "entire" in rt.lower()), None)
        if match:
            updates["room_type"] = match
    elif "private room" in text or ("private" in text and "room" in text):
        match = next((rt for rt in room_types if "private" in rt.lower()), None)
        if match:
            updates["room_type"] = match
    elif "shared" in text:
        match = next((rt for rt in room_types if "shared" in rt.lower()), None)
        if match:
            updates["room_type"] = match

    guest_match = re.search(r"(\d+)\s*(?:guests?|people|pax|persons?|adults?)", text)
    if guest_match:
        updates["guests"] = int(guest_match.group(1))

    range_match = re.search(r"\$?\s*(\d+)\s*(?:-|to|and)\s*\$?\s*(\d+)", text)
    budget_match = re.search(r"(?:under|below|up ?to|max(?:imum)?|budget of|around|about|less than)\s*\$?\s*(\d+)", text)

    if range_match:
        lo, hi = sorted([float(range_match.group(1)), float(range_match.group(2))])
        updates["budget_min"] = lo
        updates["budget_max"] = hi
    elif budget_match:
        updates["budget_max"] = float(budget_match.group(1))
    elif "guests" not in updates:
        # A single bare number with no other context is most often the
        # budget in this domain ("150 a night", "$200") — take it as
        # budget_max if nothing more specific matched.
        bare_number = re.search(r"\$?\s*(\d{2,5})\b", text)
        if bare_number and not guest_match:
            updates["budget_max"] = float(bare_number.group(1))

    return updates


@router.post("/chatbot/message", response_model=schemas.ChatResponse)
def chatbot_message(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    disclaimer = (
        "This assistant uses simple keyword matching to understand your message "
        "and the same trained pricing/recommendation model used elsewhere in "
        "StaySphere — it is not a general-purpose AI chatbot. See docs/RESPONSIBLE_AI.md."
    )

    text_lower = payload.message.lower().strip()
    if any(p in text_lower for p in RESET_PHRASES):
        empty_state = schemas.ChatState()
        return schemas.ChatResponse(
            reply="No problem, let's start fresh. What's your budget per night, and how many guests?",
            state=empty_state, recommendations=[], ready=False, disclaimer=disclaimer,
        )

    cities = known_cities(db)
    room_types = known_room_types(db)
    updates = extract_slots(payload.message, cities, room_types)

    state = payload.state.model_copy(update=updates)

    have_budget = state.budget_max is not None
    have_guests = state.guests is not None

    understood_bits = []
    if "city" in updates:
        understood_bits.append(f"in {state.city}")
    if "room_type" in updates:
        understood_bits.append(f"a {state.room_type.lower()}")
    if "guests" in updates:
        understood_bits.append(f"for {state.guests} guest{'s' if state.guests != 1 else ''}")
    if "budget_max" in updates:
        budget_phrase = f"budget ${state.budget_min:.0f}\u2013${state.budget_max:.0f}" if state.budget_min else f"budget up to ${state.budget_max:.0f}"
        understood_bits.append(budget_phrase)
    understood_line = f"Got it \u2014 {', '.join(understood_bits)}. " if understood_bits else ""

    if not have_budget:
        reply = understood_line + "What's your budget per night (e.g. \"under $150\")?"
        return schemas.ChatResponse(reply=reply, state=state, recommendations=[], ready=False, disclaimer=disclaimer)

    if not have_guests:
        reply = understood_line + "How many guests will be staying?"
        return schemas.ChatResponse(reply=reply, state=state, recommendations=[], ready=False, disclaimer=disclaimer)

    total_candidates, results = generate_recommendations(
        db,
        budget_min=state.budget_min or 0,
        budget_max=state.budget_max,
        guests=state.guests,
        city=state.city,
        room_type=state.room_type,
        limit=5,
    )

    if not results:
        reply = understood_line + (
            f"I couldn't find any rooms matching that exactly (checked {total_candidates} candidates). "
            "Want to widen your budget or try a different city?"
        )
        return schemas.ChatResponse(reply=reply, state=state, recommendations=[], ready=True, disclaimer=disclaimer)

    top = results[0]
    over_budget_note = ""
    if top.price > state.budget_max:
        over_budget_note = f" (note: ${top.price} is slightly above your ${state.budget_max:.0f} budget, shown because it's the closest strong match \u2014 ask to lower the budget further to exclude it)"
    reply = understood_line + (
        f"Here are {len(results)} good matches out of {total_candidates} rooms I checked. "
        f"Top pick: \"{top.name}\" in {top.neighbourhood}, {top.city} at ${top.price}/night{over_budget_note}"
        + (f" \u2014 a great deal, the model estimates it's normally worth ${top.fair_price_estimate}" if top.is_great_value else "")
        + ". Tell me if you want to change your budget, city, or guest count and I'll re-rank."
    )
    return schemas.ChatResponse(reply=reply, state=state, recommendations=results, ready=True, disclaimer=disclaimer)
