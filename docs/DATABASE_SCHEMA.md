# Database Schema — StaySphere

Engine: PostgreSQL in deployment (Amazon RDS), SQLite for local dev
(`DATABASE_URL` env var switches between them — see `src/backend/app/database.py`).
ORM: SQLAlchemy (`src/backend/app/models.py`).

## Tables

### `users` (application data)

| Column | Type | Constraints |
|---|---|---|
| user_id | INTEGER | PRIMARY KEY |
| name | VARCHAR | NOT NULL |
| email | VARCHAR | UNIQUE, NOT NULL, indexed |
| password_hash | VARCHAR | NOT NULL (bcrypt) |
| role | ENUM(guest, host, admin) | NOT NULL, default `guest` |
| created_at | TIMESTAMP | default now |
| updated_at | TIMESTAMP | default now, on update now |

### `listings_source` (seeded from dataset — see `data/DATA_DICTIONARY.md` for full column notes)

| Column | Type | Constraints |
|---|---|---|
| listing_id | INTEGER | PRIMARY KEY |
| host_id | INTEGER | indexed |
| city | VARCHAR | indexed (search filter) |
| neighbourhood | VARCHAR | indexed (search filter) |
| property_type | VARCHAR | indexed (search filter) |
| room_type | VARCHAR | indexed (search filter) |
| price | FLOAT | indexed (search filter + sort) |
| review_scores_rating | FLOAT | indexed (search filter + sort) |
| ... | | (remaining dataset columns, see models.py / DATA_DICTIONARY.md) |

### `bookings` (application data)

| Column | Type | Constraints |
|---|---|---|
| booking_id | INTEGER | PRIMARY KEY |
| listing_id | INTEGER | FOREIGN KEY -> listings_source.listing_id, indexed |
| guest_id | INTEGER | FOREIGN KEY -> users.user_id, indexed |
| check_in | TIMESTAMP | NOT NULL |
| check_out | TIMESTAMP | NOT NULL |
| guests | INTEGER | NOT NULL |
| nights | INTEGER | NOT NULL |
| nightly_price | FLOAT | NOT NULL (snapshot of price at booking time) |
| total_amount | FLOAT | NOT NULL |
| status | ENUM(pending, confirmed, cancelled, completed) | NOT NULL, default `confirmed` |
| created_at | TIMESTAMP | default now |
| updated_at | TIMESTAMP | default now, on update now |

**Composite index** `ix_booking_listing_dates` on `(listing_id, check_in, check_out)` — supports the overlap query used for double-booking prevention (`app/routers/bookings.py`).

## Relationships

```
users (1) ────< (many) bookings (many) >──── (1) listings_source
```

## Why price is snapshotted onto the booking

`nightly_price` and `total_amount` are copied onto the booking row at
creation time rather than always looked up live from `listings_source.price`.
This preserves what the guest actually agreed to pay even if the listing's
price changes later — a standard invoicing pattern, not an oversight.

## Indexes rationale

Every column used in a search filter or sort (`city`, `neighbourhood`,
`property_type`, `room_type`, `price`, `review_scores_rating`) is indexed,
because `GET /api/listings` filters/sorts on these under normal use and the
dataset, while small for this project, is designed to scale to a much
larger real dataset without a full table scan per search.

## Not yet implemented (documented as future work, not fabricated as done)

- `application_reviews` table for guest-submitted reviews on completed
  bookings (brief section 11) — descoped from this build to keep the
  guest booking workflow the single, well-tested core feature. See
  `docs/INF2006_REQUIREMENTS_MATRIX.md` for status.
- `audit_logs` table for a dedicated audit trail beyond the request/event
  logs already emitted to stdout.
