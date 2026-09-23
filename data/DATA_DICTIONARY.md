# Data Dictionary

Definitions below are taken from the data dictionaries supplied with the archive. The project does not treat identifier fields as model inputs.

## Listings.csv

| Field | Type | Description | Notes |
|-------|------|-------------|-------|
| `listing_id` | integer | Listing identifier | Unique in the observed file |
| `name` | string | Listing name | Free text, excluded from modelling |
| `host_id` | integer | Host identifier | Excluded from modelling |
| `host_since` | date | Date the host joined Airbnb | Nullable |
| `host_location` | string | Host location | Nullable, free text |
| `host_response_time` | category | Estimated response time | Nullable |
| `host_response_rate` | percentage | Host response rate | Nullable |
| `host_acceptance_rate` | percentage | Host acceptance rate | Nullable |
| `host_is_superhost` | boolean-like | Whether the host is a superhost | Stored as `t` or `f`, nullable |
| `host_total_listings_count` | numeric | Host's total Airbnb listings | Nullable |
| `host_has_profile_pic` | boolean-like | Whether the host has a profile picture | Stored as `t` or `f`, nullable |
| `host_identity_verified` | boolean-like | Whether the host identity is verified | Stored as `t` or `f`, nullable |
| `neighbourhood` | category | Listing neighbourhood | 660 observed values |
| `district` | category | Listing district | 86.8% missing |
| `city` | category | Listing city | 10 observed values |
| `latitude` | numeric | Listing latitude | Required in observed data |
| `longitude` | numeric | Listing longitude | Required in observed data |
| `property_type` | category | Listing property type | 144 observed values |
| `room_type` | category | Airbnb room type | 4 observed values |
| `accommodates` | integer | Guest capacity | Required in observed data |
| `bedrooms` | numeric | Bedroom count | 10.5% missing |
| `amenities` | string/list | Amenities included | Serialized list, not yet modelled |
| `price` | numeric | Nightly price in the city's local currency | Prediction target |
| `minimum_nights` | integer | Minimum nights per booking | Required in observed data |
| `maximum_nights` | integer | Maximum nights per booking | Required in observed data |
| `review_scores_rating` | numeric | Overall rating out of 100 | 32.7% missing |
| `review_scores_accuracy` | numeric | Accuracy score out of 10 | Nullable |
| `review_scores_cleanliness` | numeric | Cleanliness score out of 10 | Nullable |
| `review_scores_checkin` | numeric | Check-in score out of 10 | Nullable |
| `review_scores_communication` | numeric | Communication score out of 10 | Nullable |
| `review_scores_location` | numeric | Location score out of 10 | Nullable |
| `review_scores_value` | numeric | Value score out of 10 | Nullable and potentially target-related |
| `instant_bookable` | boolean-like | Whether the listing can be booked instantly | Stored as `t` or `f` |

## Reviews.csv

| Field | Type | Description | Notes |
|-------|------|-------------|-------|
| `listing_id` | integer | Listing identifier | Joins to Listings |
| `review_id` | integer | Review identifier | No review text is present |
| `date` | date | Review date | Observed from 2008-11-16 to 2021-03-01 |
| `reviewer_id` | integer | Reviewer identifier | Must not be exposed as user data |
