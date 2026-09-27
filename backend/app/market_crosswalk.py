"""Explicit, reviewed metro crosswalk between Redfin's and Apartment
List's naming conventions - generated once from the actual downloaded
files (see docs/ROADMAP.md Phase 3) and hand-checked, not recomputed by
fuzzy matching at ingest time. A metro with aptlist_name=None is a real
gap: Redfin tracks it as its own metropolitan division (e.g. Anaheim,
Fort Lauderdale, Oakland) while Apartment List only publishes the larger
combined metro it belongs to (Los Angeles, Miami, San Francisco). Those
are genuinely different geographies - this crosswalk does not paper over
that by borrowing the parent metro's numbers.
"""

# (id, canonical_name, state, redfin_name, aptlist_name)
METRO_CROSSWALK = [
    ("anaheim-ca", "Anaheim, CA", "CA", "Anaheim, CA metro area", None),
    ("atlanta-ga", "Atlanta, GA", "GA", "Atlanta, GA metro area", "Atlanta-Sandy Springs-Alpharetta, GA"),
    ("austin-tx", "Austin, TX", "TX", "Austin, TX metro area", "Austin-Round Rock-Georgetown, TX"),
    ("baltimore-md", "Baltimore, MD", "MD", "Baltimore, MD metro area", "Baltimore-Columbia-Towson, MD"),
    ("boston-ma", "Boston, MA", "MA", "Boston, MA metro area", "Boston-Cambridge-Newton, MA-NH"),
    ("charlotte-nc", "Charlotte, NC", "NC", "Charlotte, NC metro area", "Charlotte-Concord-Gastonia, NC-SC"),
    ("chicago-il", "Chicago, IL", "IL", "Chicago, IL metro area", "Chicago-Naperville-Elgin, IL-IN-WI"),
    ("cincinnati-oh", "Cincinnati, OH", "OH", "Cincinnati, OH metro area", "Cincinnati, OH-KY-IN"),
    ("cleveland-oh", "Cleveland, OH", "OH", "Cleveland, OH metro area", "Cleveland-Elyria, OH"),
    ("columbus-oh", "Columbus, OH", "OH", "Columbus, OH metro area", "Columbus, OH"),
    ("dallas-tx", "Dallas, TX", "TX", "Dallas, TX metro area", "Dallas-Fort Worth-Arlington, TX"),
    ("denver-co", "Denver, CO", "CO", "Denver, CO metro area", "Denver-Aurora-Lakewood, CO"),
    ("detroit-mi", "Detroit, MI", "MI", "Detroit, MI metro area", "Detroit-Warren-Dearborn, MI"),
    ("fort-lauderdale-fl", "Fort Lauderdale, FL", "FL", "Fort Lauderdale, FL metro area", None),
    ("fort-worth-tx", "Fort Worth, TX", "TX", "Fort Worth, TX metro area", None),
    ("houston-tx", "Houston, TX", "TX", "Houston, TX metro area", "Houston-The Woodlands-Sugar Land, TX"),
    ("indianapolis-in", "Indianapolis, IN", "IN", "Indianapolis, IN metro area", "Indianapolis-Carmel-Anderson, IN"),
    ("jacksonville-fl", "Jacksonville, FL", "FL", "Jacksonville, FL metro area", "Jacksonville, FL"),
    ("kansas-city-mo", "Kansas City, MO", "MO", "Kansas City, MO metro area", "Kansas City, MO-KS"),
    ("las-vegas-nv", "Las Vegas, NV", "NV", "Las Vegas, NV metro area", "Las Vegas-Henderson-Paradise, NV"),
    ("los-angeles-ca", "Los Angeles, CA", "CA", "Los Angeles, CA metro area", "Los Angeles-Long Beach-Anaheim, CA"),
    ("miami-fl", "Miami, FL", "FL", "Miami, FL metro area", "Miami-Fort Lauderdale-Pompano Beach, FL"),
    ("milwaukee-wi", "Milwaukee, WI", "WI", "Milwaukee, WI metro area", "Milwaukee-Waukesha, WI"),
    ("minneapolis-mn", "Minneapolis, MN", "MN", "Minneapolis, MN metro area", "Minneapolis-St. Paul-Bloomington, MN-WI"),
    ("montgomery-county-pa", "Montgomery County, PA", "PA", "Montgomery County, PA metro area", None),
    ("nashville-tn", "Nashville, TN", "TN", "Nashville, TN metro area", "Nashville-Davidson--Murfreesboro--Franklin, TN"),
    ("nassau-county-ny", "Nassau County, NY", "NY", "Nassau County, NY metro area", None),
    ("new-brunswick-nj", "New Brunswick, NJ", "NJ", "New Brunswick, NJ metro area", None),
    ("new-york-ny", "New York, NY", "NY", "New York, NY metro area", "New York-Newark-Jersey City, NY-NJ-PA"),
    ("newark-nj", "Newark, NJ", "NJ", "Newark, NJ metro area", None),
    ("oakland-ca", "Oakland, CA", "CA", "Oakland, CA metro area", None),
    ("orlando-fl", "Orlando, FL", "FL", "Orlando, FL metro area", "Orlando-Kissimmee-Sanford, FL"),
    ("philadelphia-pa", "Philadelphia, PA", "PA", "Philadelphia, PA metro area", "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD"),
    ("phoenix-az", "Phoenix, AZ", "AZ", "Phoenix, AZ metro area", "Phoenix-Mesa-Chandler, AZ"),
    ("pittsburgh-pa", "Pittsburgh, PA", "PA", "Pittsburgh, PA metro area", "Pittsburgh, PA"),
    ("portland-or", "Portland, OR", "OR", "Portland, OR metro area", "Portland-Vancouver-Hillsboro, OR-WA"),
    ("providence-ri", "Providence, RI", "RI", "Providence, RI metro area", "Providence-Warwick, RI-MA"),
    ("riverside-ca", "Riverside, CA", "CA", "Riverside, CA metro area", "Riverside-San Bernardino-Ontario, CA"),
    ("sacramento-ca", "Sacramento, CA", "CA", "Sacramento, CA metro area", "Sacramento-Roseville-Folsom, CA"),
    ("san-antonio-tx", "San Antonio, TX", "TX", "San Antonio, TX metro area", "San Antonio-New Braunfels, TX"),
    ("san-diego-ca", "San Diego, CA", "CA", "San Diego, CA metro area", "San Diego-Chula Vista-Carlsbad, CA"),
    ("san-francisco-ca", "San Francisco, CA", "CA", "San Francisco, CA metro area", "San Francisco-Oakland-Berkeley, CA"),
    ("san-jose-ca", "San Jose, CA", "CA", "San Jose, CA metro area", "San Jose-Sunnyvale-Santa Clara, CA"),
    ("seattle-wa", "Seattle, WA", "WA", "Seattle, WA metro area", "Seattle-Tacoma-Bellevue, WA"),
    ("st-louis-mo", "St. Louis, MO", "MO", "St. Louis, MO metro area", "St. Louis, MO-IL"),
    ("tampa-fl", "Tampa, FL", "FL", "Tampa, FL metro area", "Tampa-St. Petersburg-Clearwater, FL"),
    ("virginia-beach-va", "Virginia Beach, VA", "VA", "Virginia Beach, VA metro area", "Virginia Beach-Norfolk-Newport News, VA-NC"),
    ("warren-mi", "Warren, MI", "MI", "Warren, MI metro area", None),
    ("washington-dc", "Washington, DC", "DC", "Washington, DC metro area", "Washington-Arlington-Alexandria, DC-VA-MD-WV"),
    ("west-palm-beach-fl", "West Palm Beach, FL", "FL", "West Palm Beach, FL metro area", None),
]
