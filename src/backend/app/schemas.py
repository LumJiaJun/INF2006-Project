from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---- Auth ----

class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    role: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---- Listings ----

class ListingOut(BaseModel):
    listing_id: int
    name: str
    city: str
    neighbourhood: str
    district: str
    property_type: str
    room_type: str
    accommodates: int
    bedrooms: int
    amenities: str
    price: float
    minimum_nights: int
    maximum_nights: int
    review_scores_rating: Optional[float]
    review_scores_accuracy: Optional[float]
    review_scores_cleanliness: Optional[float]
    review_scores_checkin: Optional[float]
    review_scores_communication: Optional[float]
    review_scores_location: Optional[float]
    review_scores_value: Optional[float]
    host_is_superhost: bool
    host_identity_verified: bool
    host_has_profile_pic: bool
    host_response_time: Optional[str]
    host_response_rate: Optional[int]
    host_acceptance_rate: Optional[int]
    instant_bookable: bool
    photo_url: Optional[str] = None
    latitude: Optional[float]
    longitude: Optional[float]

    model_config = {"from_attributes": True}


class ListingSearchResult(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[ListingOut]


# ---- Bookings ----

class BookingCreate(BaseModel):
    listing_id: int
    check_in: datetime
    check_out: datetime
    guests: int = Field(gt=0)

    @field_validator("check_out")
    @classmethod
    def check_out_after_check_in(cls, v, info):
        check_in = info.data.get("check_in")
        if check_in and v <= check_in:
            raise ValueError("check_out must be after check_in")
        return v


class BookingOut(BaseModel):
    booking_id: int
    listing_id: int
    guest_id: int
    check_in: datetime
    check_out: datetime
    guests: int
    nights: int
    nightly_price: float
    total_amount: float
    status: str
    created_at: datetime
    has_review: bool = False
    can_review: bool = False

    model_config = {"from_attributes": True}


# ---- ML ----

class PriceEstimateRequest(BaseModel):
    city: str
    property_type: str
    room_type: str
    accommodates: int = Field(gt=0, le=20)
    bedrooms: int = Field(gt=0, le=10)
    minimum_nights: int = Field(gt=0, le=365)
    review_scores_rating: float = Field(ge=0, le=5, default=4.5)


class PriceEstimateResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    estimated_price: float
    range_low: float
    range_high: float
    key_factors: List[str]
    model_version: str
    disclaimer: str


# ---- Analytics ----

class AnalyticsOverview(BaseModel):
    total_listings: int
    average_price: float
    median_price: float
    average_rating: float
    most_common_room_type: str
    most_common_city: str


# ---- Recommendations ----

class RecommendationRequest(BaseModel):
    budget_min: float = Field(ge=0, default=0)
    budget_max: float = Field(gt=0)
    guests: int = Field(gt=0, le=20, default=1)
    city: Optional[str] = None
    room_type: Optional[str] = None

    @field_validator("budget_max")
    @classmethod
    def budget_max_at_least_min(cls, v, info):
        budget_min = info.data.get("budget_min", 0)
        if v < budget_min:
            raise ValueError("budget_max must be >= budget_min")
        return v


class RecommendedListing(ListingOut):
    fair_price_estimate: float
    is_great_value: bool
    match_reason: str


class RecommendationResponse(BaseModel):
    total_candidates: int
    results: List[RecommendedListing]
    disclaimer: str


# ---- Availability ----

class BookedRange(BaseModel):
    check_in: datetime
    check_out: datetime


class AvailabilityResponse(BaseModel):
    listing_id: int
    minimum_nights: int
    maximum_nights: int
    booked_ranges: List[BookedRange]


# ---- Reviews ----

class ReviewCreate(BaseModel):
    booking_id: int
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=1000)


class ReviewOut(BaseModel):
    review_id: int
    booking_id: int
    listing_id: int
    guest_id: int
    guest_name: str
    rating: int
    comment: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Chatbot ----

class ChatState(BaseModel):
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    guests: Optional[int] = None
    city: Optional[str] = None
    room_type: Optional[str] = None
    city_skip: bool = False
    room_type_skip: bool = False


class QuickReply(BaseModel):
    label: str
    value: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    state: ChatState = Field(default_factory=ChatState)


class ChatResponse(BaseModel):
    reply: str
    state: ChatState
    recommendations: List[RecommendedListing] = Field(default_factory=list)
    quick_replies: List[QuickReply] = Field(default_factory=list)
    ready: bool
    disclaimer: str
