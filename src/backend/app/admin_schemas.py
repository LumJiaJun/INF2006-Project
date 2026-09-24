from typing import Optional, List
from pydantic import BaseModel


class ListingCreate(BaseModel):
    name: str
    host_id: int = 1
    host_since: str = "2024-01-01"
    host_location: str = "Singapore"
    host_response_time: str = "within an hour"
    host_response_rate: int = 95
    host_acceptance_rate: int = 95
    host_is_superhost: bool = False
    host_total_listings_count: int = 1
    host_has_profile_pic: bool = True
    host_identity_verified: bool = True
    neighbourhood: str
    district: str = "Central"
    city: str
    latitude: float = 1.3521
    longitude: float = 103.8198
    property_type: str
    room_type: str
    accommodates: int
    bedrooms: int
    amenities: str = "Wifi|Air conditioning"
    price: float
    minimum_nights: int = 1
    maximum_nights: int = 30
    review_scores_rating: float = 4.5
    review_scores_accuracy: float = 4.5
    review_scores_cleanliness: float = 4.5
    review_scores_checkin: float = 4.5
    review_scores_communication: float = 4.5
    review_scores_location: float = 4.5
    review_scores_value: float = 4.5
    instant_bookable: bool = True


class ListingUpdate(BaseModel):
    """All fields optional — only supplied fields are changed."""
    name: Optional[str] = None
    neighbourhood: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    property_type: Optional[str] = None
    room_type: Optional[str] = None
    accommodates: Optional[int] = None
    bedrooms: Optional[int] = None
    amenities: Optional[str] = None
    price: Optional[float] = None
    minimum_nights: Optional[int] = None
    maximum_nights: Optional[int] = None
    instant_bookable: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    host_is_superhost: Optional[bool] = None
    host_identity_verified: Optional[bool] = None
    host_has_profile_pic: Optional[bool] = None
    host_response_time: Optional[str] = None
    host_response_rate: Optional[int] = None
    host_acceptance_rate: Optional[int] = None
    review_scores_rating: Optional[float] = None
    review_scores_accuracy: Optional[float] = None
    review_scores_cleanliness: Optional[float] = None
    review_scores_checkin: Optional[float] = None
    review_scores_communication: Optional[float] = None
    review_scores_location: Optional[float] = None
    review_scores_value: Optional[float] = None


class AdminAnalytics(BaseModel):
    total_listings: int
    total_users: int
    total_bookings: int
    confirmed_bookings: int
    cancelled_bookings: int
    total_revenue: float
    average_price: float
    average_rating: float
    most_common_city: str


class AdminBookingOut(BaseModel):
    booking_id: int
    listing_id: int
    listing_name: str
    guest_id: int
    guest_name: str
    guest_email: str
    check_in: str
    check_out: str
    guests: int
    nights: int
    total_amount: float
    status: str
    created_at: str


class CityInsight(BaseModel):
    city: str
    listing_count: int
    average_price: float
    average_rating: float
    total_bookings: int
    demand_index: float  # 0-1, relative to the busiest city, for the "heatmap" bar/circle intensity
    latitude: float   # centroid of this city's listings, for the geographic heatmap view
    longitude: float


class LocationInsight(BaseModel):
    city: str
    neighbourhood: str
    listing_count: int
    average_price: float
    average_rating: float
    total_bookings: int
    demand_index: float
    latitude: float
    longitude: float


class PricingInsightsResponse(BaseModel):
    cities: List[CityInsight]
    neighbourhoods: List[LocationInsight]
    note: str


class AdminListingOut(BaseModel):
    listing_id: int
    name: str
    city: str
    neighbourhood: str
    property_type: str
    room_type: str
    price: float
    review_scores_rating: Optional[float]
    suggested_price: Optional[float] = None
    price_gap_pct: Optional[float] = None  # (price - suggested_price) / suggested_price * 100

    model_config = {"from_attributes": True}


class AdminReviewOut(BaseModel):
    review_id: int
    booking_id: int
    listing_id: int
    listing_name: str
    guest_name: str
    guest_email: str
    rating: int
    comment: Optional[str]
    created_at: str


class AdminUserOut(BaseModel):
    user_id: int
    name: str
    email: str
    role: str
    created_at: str
    booking_count: int


class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None  # "guest" | "host" | "admin"
