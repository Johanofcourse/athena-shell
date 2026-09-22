"""Generates a synthetic but realistic listing-history dataset: every listing
gets a chronological event timeline (list -> price changes -> maybe a
delist/relist cycle -> sold or still active), and the denormalized summary
fields on Listing are derived from that timeline, not made up independently.

Run with: python -m app.seed
"""

import random
import uuid
from datetime import date, timedelta

from faker import Faker

from app.database import Base, SessionLocal, engine
from app.models import EventType, Listing, ListingEvent, ListingStatus

fake = Faker()
random.seed(42)
Faker.seed(42)

NUM_LISTINGS = 180
TODAY = date.today()

METROS = [
    ("Austin", "TX"),
    ("Denver", "CO"),
    ("Raleigh", "NC"),
    ("Columbus", "OH"),
    ("Phoenix", "AZ"),
    ("Nashville", "TN"),
    ("Tampa", "FL"),
    ("Boise", "ID"),
]

PROPERTY_TYPES = {
    "single_family": (320_000, 850_000),
    "condo": (180_000, 480_000),
    "townhouse": (250_000, 600_000),
    "multi_family": (400_000, 950_000),
}


def _generate_timeline(listing_id: str) -> tuple[list[ListingEvent], dict]:
    property_type = random.choice(list(PROPERTY_TYPES.keys()))
    lo, hi = PROPERTY_TYPES[property_type]
    original_price = round(random.uniform(lo, hi), -3)

    days_ago_start = random.randint(30, 400)
    first_listed_date = TODAY - timedelta(days=days_ago_start)

    events: list[ListingEvent] = [
        ListingEvent(
            listing_id=listing_id,
            event_type=EventType.LISTED,
            event_date=first_listed_date,
            price=original_price,
            status=ListingStatus.ACTIVE,
            notes="Initial listing",
        )
    ]

    current_price = original_price
    cursor = first_listed_date
    active_period_start = first_listed_date
    relist_count = 0
    total_dom = 0
    status = ListingStatus.ACTIVE
    terminal_date = TODAY

    while True:
        cursor += timedelta(days=random.randint(10, 60))
        if cursor >= TODAY:
            break

        roll = random.random()
        if roll < 0.45:
            drop_pct = random.uniform(0.01, 0.08)
            current_price = round(current_price * (1 - drop_pct), -2)
            events.append(
                ListingEvent(
                    listing_id=listing_id,
                    event_type=EventType.PRICE_CHANGE,
                    event_date=cursor,
                    price=current_price,
                    notes=f"Price reduced {drop_pct * 100:.1f}%",
                )
            )
        elif roll < 0.55:
            bump_pct = random.uniform(0.01, 0.04)
            current_price = round(current_price * (1 + bump_pct), -2)
            events.append(
                ListingEvent(
                    listing_id=listing_id,
                    event_type=EventType.PRICE_CHANGE,
                    event_date=cursor,
                    price=current_price,
                    notes="Price increased",
                )
            )
        elif roll < 0.70:
            total_dom += (cursor - active_period_start).days
            events.append(
                ListingEvent(
                    listing_id=listing_id,
                    event_type=EventType.DELISTED,
                    event_date=cursor,
                    status=ListingStatus.OFF_MARKET,
                    notes="Taken off market",
                )
            )
            relist_gap = random.randint(5, 30)
            cursor += timedelta(days=relist_gap)
            if cursor >= TODAY:
                status = ListingStatus.OFF_MARKET
                terminal_date = cursor - timedelta(days=relist_gap)
                break
            relist_count += 1
            active_period_start = cursor
            events.append(
                ListingEvent(
                    listing_id=listing_id,
                    event_type=EventType.RELISTED,
                    event_date=cursor,
                    price=current_price,
                    status=ListingStatus.ACTIVE,
                    notes="Relisted",
                )
            )
        elif roll < 0.80:
            total_dom += (cursor - active_period_start).days
            status = ListingStatus.SOLD
            terminal_date = cursor
            sold_price = round(current_price * random.uniform(0.96, 1.0), -2)
            events.append(
                ListingEvent(
                    listing_id=listing_id,
                    event_type=EventType.SOLD,
                    event_date=cursor,
                    price=sold_price,
                    status=ListingStatus.SOLD,
                    notes="Sold",
                )
            )
            current_price = sold_price
            break
        # else: time passes, no event this cycle

    if status == ListingStatus.ACTIVE:
        total_dom += (TODAY - active_period_start).days
        days_on_market = (TODAY - active_period_start).days
        last_event_date = events[-1].event_date
    else:
        days_on_market = (terminal_date - active_period_start).days
        last_event_date = terminal_date

    price_drop_amount = round(original_price - current_price, 2)
    price_drop_pct = round((price_drop_amount / original_price) * 100, 2) if original_price else 0.0

    summary = {
        "property_type": property_type,
        "original_price": original_price,
        "current_price": current_price,
        "price_drop_amount": price_drop_amount,
        "price_drop_pct": price_drop_pct,
        "status": status,
        "days_on_market": max(days_on_market, 0),
        "total_days_on_market": max(total_dom, 0),
        "relist_count": relist_count,
        "first_listed_date": first_listed_date,
        "last_event_date": last_event_date,
    }
    return events, summary


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Listing).first() is not None:
            print("Database already seeded, skipping.")
            return

        for _ in range(NUM_LISTINGS):
            listing_id = str(uuid.uuid4())
            city, state = random.choice(METROS)
            events, summary = _generate_timeline(listing_id)

            listing = Listing(
                id=listing_id,
                address=fake.street_address(),
                city=city,
                state=state,
                zip_code=fake.postcode(),
                bedrooms=random.randint(1, 5),
                bathrooms=random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5]),
                sqft=random.randint(650, 4200),
                **summary,
            )
            listing.events = events
            db.add(listing)

        db.commit()
        print(f"Seeded {NUM_LISTINGS} listings.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
