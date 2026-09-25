"""
A conversational interface over the SAME recommendation engine used by
POST /api/recommendations (see routers/recommendations.py). This is a
deliberate design choice for an academic project:

- It is NOT a call to an external LLM API (no API key, no per-message
  cost, nothing that could leak data to a third party, fully testable
  offline).
- It IS a real, working conversational UI: it walks the user through a
  fixed sequence of slots (budget, guests, city, room type) via
  quick-reply buttons on the frontend (so the user never has to type),
  keeps that state across turns so the user can change their mind at
  any point ("change budget"), and once enough is known, calls the
  exact same trained price model + ranking heuristic used everywhere
  else in the app.

This keeps the project's ONE evaluated AI/ML feature (the regression
model + the ranking heuristic built on it) as the single source of
truth, with the chatbot as an additional interface onto it — not a
second, unevaluated "AI" bolted on for its own sake.

The frontend sends plain-text messages synthesized from button clicks
(e.g. clicking "$50-100" sends "$50 to $100"), so the same slot-
extraction logic below would also work with genuinely typed free text
if that were ever re-enabled — the NLU itself doesn't assume buttons.
"""
import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .recommendations import generate_recommendations

router = APIRouter(prefix="/api", tags=["chatbot"])

RESET_PHRASES = ("start over", "reset", "start again", "new search")
CHANGE_COMMANDS = {
    "change budget": {"budget_min": None, "budget_max": None},
    "change guests": {"guests": None},
    "change city": {"city": None, "city_skip": False},
    "change room type": {"room_type": None, "room_type_skip": False},
}


def known_cities(db: Session) -> list[str]:
    return sorted(c for (c,) in db.query(models.Listing.city).distinct().all())


def known_room_types(db: Session) -> list[str]:
    return sorted(r for (r,) in db.query(models.Listing.room_type).distinct().all())


def extract_slots(message: str, cities: list[str], room_types: list[str]) -> dict:
    text = message.lower().strip()

    if text in CHANGE_COMMANDS:
        return dict(CHANGE_COMMANDS[text])
    if text == "any city":
        return {"city_skip": True}
    if text == "any room type":
        return {"room_type_skip": True}

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

    guest_match = re.search(r"(\d+)\s*(?:guests?|people|pax|persons?|adults?)?", text)
    if "guest" in text and guest_match:
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
        bare_number = re.search(r"\$?\s*(\d{2,5})\b", text)
        if bare_number and not guest_match:
            updates["budget_max"] = float(bare_number.group(1))

    return updates


def quick_replies_for(stage: str, db: Session) -> list[schemas.QuickReply]:
    if stage == "budget":
        return [
            schemas.QuickReply(label="Under $50", value="under $50"),
            schemas.QuickReply(label="$50\u2013100", value="$50 to $100"),
            schemas.QuickReply(label="$100\u2013200", value="$100 to $200"),
            schemas.QuickReply(label="$200\u2013300", value="$200 to $300"),
            schemas.QuickReply(label="$300\u2013500", value="$300 to $500"),
        ]
    if stage == "guests":
        return [schemas.QuickReply(label=str(n) if n < 5 else "5+", value=f"{n} guests") for n in (1, 2, 3, 4, 5)]
    if stage == "city":
        replies = [schemas.QuickReply(label=c, value=c) for c in known_cities(db)]
        replies.append(schemas.QuickReply(label="Any city", value="any city"))
        return replies
    if stage == "room_type":
        replies = [schemas.QuickReply(label=rt, value=rt) for rt in known_room_types(db)]
        replies.append(schemas.QuickReply(label="Any room type", value="any room type"))
        return replies
    if stage == "ready":
        return [
            schemas.QuickReply(label="\U0001F504 Change budget", value="change budget"),
            schemas.QuickReply(label="\U0001F465 Change guests", value="change guests"),
            schemas.QuickReply(label="\U0001F4CD Change city", value="change city"),
            schemas.QuickReply(label="\U0001F6CF\uFE0F Change room type", value="change room type"),
            schemas.QuickReply(label="\U0001F501 Start over", value="start over"),
        ]
    return []


@router.post("/chatbot/message", response_model=schemas.ChatResponse)
def chatbot_message(payload: schemas.ChatRequest, db: Session = Depends(get_db)):
    disclaimer = (
        "This assistant uses simple keyword matching to understand your choices and "
        "the same trained pricing/recommendation model used elsewhere in StaySphere "
        "\u2014 it is not a general-purpose AI chatbot. See docs/RESPONSIBLE_AI.md."
    )

    text_lower = payload.message.lower().strip()
    if any(p == text_lower or p in text_lower for p in RESET_PHRASES):
        empty_state = schemas.ChatState()
        return schemas.ChatResponse(
            reply="No problem, let's start fresh. What's your budget per night?",
            state=empty_state, recommendations=[], quick_replies=quick_replies_for("budget", db),
            ready=False, disclaimer=disclaimer,
        )

    cities = known_cities(db)
    room_types = known_room_types(db)
    updates = extract_slots(payload.message, cities, room_types)
    state = payload.state.model_copy(update=updates)

    understood_bits = []
    if "city" in updates and updates["city"]:
        understood_bits.append(f"in {state.city}")
    if "room_type" in updates and updates["room_type"]:
        understood_bits.append(f"a {state.room_type.lower()}")
    if "guests" in updates and updates["guests"]:
        understood_bits.append(f"for {state.guests} guest{'s' if state.guests != 1 else ''}")
    if "budget_max" in updates and updates["budget_max"]:
        budget_phrase = f"budget ${state.budget_min:.0f}\u2013${state.budget_max:.0f}" if state.budget_min else f"budget up to ${state.budget_max:.0f}"
        understood_bits.append(budget_phrase)
    understood_line = f"Got it \u2014 {', '.join(understood_bits)}. " if understood_bits else ""

    # Fixed question sequence: budget -> guests -> city -> room type -> ready.
    if state.budget_max is None:
        reply = understood_line + "What's your budget per night?"
        return schemas.ChatResponse(reply=reply, state=state, recommendations=[],
                                     quick_replies=quick_replies_for("budget", db), ready=False, disclaimer=disclaimer)

    if state.guests is None:
        reply = understood_line + "How many guests will be staying?"
        return schemas.ChatResponse(reply=reply, state=state, recommendations=[],
                                     quick_replies=quick_replies_for("guests", db), ready=False, disclaimer=disclaimer)

    if state.city is None and not state.city_skip:
        reply = understood_line + "Any particular city, or should I search everywhere?"
        return schemas.ChatResponse(reply=reply, state=state, recommendations=[],
                                     quick_replies=quick_replies_for("city", db), ready=False, disclaimer=disclaimer)

    if state.room_type is None and not state.room_type_skip:
        reply = understood_line + "Any preferred room type?"
        return schemas.ChatResponse(reply=reply, state=state, recommendations=[],
                                     quick_replies=quick_replies_for("room_type", db), ready=False, disclaimer=disclaimer)

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
            "Want to change your budget or city?"
        )
        return schemas.ChatResponse(reply=reply, state=state, recommendations=[],
                                     quick_replies=quick_replies_for("ready", db), ready=True, disclaimer=disclaimer)

    top = results[0]
    over_budget_note = ""
    if top.price > state.budget_max:
        over_budget_note = f" (note: ${top.price} is slightly above your ${state.budget_max:.0f} budget, shown as the closest strong match)"
    reply = understood_line + (
        f"Here are {len(results)} good matches out of {total_candidates} rooms I checked. "
        f"Top pick: \"{top.name}\" in {top.neighbourhood}, {top.city} at ${top.price}/night{over_budget_note}"
        + (f" \u2014 a great deal, the model estimates it's normally worth ${top.fair_price_estimate}" if top.is_great_value else "")
        + ". Want to adjust anything?"
    )
    return schemas.ChatResponse(reply=reply, state=state, recommendations=results,
                                 quick_replies=quick_replies_for("ready", db), ready=True, disclaimer=disclaimer)
