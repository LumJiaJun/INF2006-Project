from fastapi import APIRouter

from .. import schemas, pricing

router = APIRouter(prefix="/api/ml", tags=["ml"])


@router.post("/price-estimate", response_model=schemas.PriceEstimateResponse)
def price_estimate(payload: schemas.PriceEstimateRequest):
    prediction = pricing.estimate_price(
        city=payload.city,
        property_type=payload.property_type,
        room_type=payload.room_type,
        accommodates=payload.accommodates,
        bedrooms=payload.bedrooms,
        minimum_nights=payload.minimum_nights,
        review_scores_rating=payload.review_scores_rating,
    )
    margin = pricing.mae()

    return schemas.PriceEstimateResponse(
        estimated_price=prediction,
        range_low=round(max(15.0, prediction - margin), 2),
        range_high=round(prediction + margin, 2),
        key_factors=pricing.key_factors(),
        model_version=pricing.model_version(),
        disclaimer=(
            "This is an academic estimate trained on a small synthetic/sample dataset. "
            "It is not a real market pricing engine and should not be used for actual "
            "pricing decisions."
        ),
    )
