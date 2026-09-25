"""
Shared access to the trained price model, so both the standalone
price-estimator endpoint and the recommendation engine score listings
using the exact same model rather than two divergent copies.
"""
import os
import joblib
import pandas as pd
from fastapi import HTTPException

MODEL_PATH = os.path.join(os.path.dirname(__file__), "ml_model", "price_model.joblib")
_bundle = None


def load_bundle():
    global _bundle
    if _bundle is None:
        if not os.path.exists(MODEL_PATH):
            raise HTTPException(
                status_code=503,
                detail="Price model not trained yet. Run analytics/train_price_model.py first.",
            )
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def estimate_price(city: str, property_type: str, room_type: str, accommodates: int,
                    bedrooms: int, minimum_nights: int, review_scores_rating: float) -> float:
    """Returns the model's fair-price estimate for a given set of listing features."""
    bundle = load_bundle()
    model = bundle["model"]
    encoders = bundle["encoders"]
    feature_columns = bundle["feature_columns"]

    row = {
        "city": city,
        "property_type": property_type,
        "room_type": room_type,
        "accommodates": accommodates,
        "bedrooms": bedrooms,
        "minimum_nights": minimum_nights,
        "review_scores_rating": review_scores_rating,
    }
    df = pd.DataFrame([row])
    for col, encoder in encoders.items():
        if row[col] not in encoder.classes_:
            df[col] = encoder.transform([encoder.classes_[0]])
        else:
            df[col] = encoder.transform(df[col])

    X = df[feature_columns]
    prediction = float(model.predict(X)[0])
    return max(15.0, round(prediction, 2))


def key_factors():
    bundle = load_bundle()
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]
    if hasattr(model, "feature_importances_"):
        importances = sorted(zip(feature_columns, model.feature_importances_), key=lambda x: x[1], reverse=True)
        return [f for f, _ in importances[:4]]
    if hasattr(model, "coef_"):
        # Linear models don't have feature_importances_; the magnitude
        # of each standardized coefficient is the equivalent signal —
        # how much a unit change in that feature moves the prediction.
        importances = sorted(zip(feature_columns, abs(model.coef_)), key=lambda x: x[1], reverse=True)
        return [f for f, _ in importances[:4]]
    return []


def mae() -> float:
    return load_bundle()["metrics"]["mae"]


def model_version() -> str:
    return load_bundle().get("model_version", "unknown")
