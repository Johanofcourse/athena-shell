"""Explicit, reviewed metro crosswalk between Redfin's, Apartment List's,
and Census's naming conventions - generated once from the actual
downloaded files (see docs/ROADMAP.md Phase 3) and hand-checked, not
recomputed by fuzzy matching at ingest time. A metro with aptlist_name or
census_income_name = None is a real gap: Redfin tracks it as its own
metropolitan division (e.g. Anaheim, Fort Lauderdale, Oakland) while
Apartment List and Census's metro-level income table only publish the
larger combined metro it belongs to (Los Angeles, Miami, San Francisco).
Those are genuinely different geographies - this crosswalk does not paper
over that by borrowing the parent metro's numbers. (The same 10 metros
are missing both aptlist_name and census_income_name - Census simply
doesn't break metro divisions out below the combined-CBSA level either.)
"""

# (id, canonical_name, state, redfin_name, aptlist_name, census_income_name)
METRO_CROSSWALK = [
    ("anaheim-ca", "Anaheim, CA", "CA", "Anaheim, CA metro area", None, None),
    ("atlanta-ga", "Atlanta, GA", "GA", "Atlanta, GA metro area", "Atlanta-Sandy Springs-Alpharetta, GA", "Atlanta-Sandy Springs-Roswell, GA Metro Area"),
    ("austin-tx", "Austin, TX", "TX", "Austin, TX metro area", "Austin-Round Rock-Georgetown, TX", "Austin-Round Rock-San Marcos, TX Metro Area"),
    ("baltimore-md", "Baltimore, MD", "MD", "Baltimore, MD metro area", "Baltimore-Columbia-Towson, MD", "Baltimore-Columbia-Towson, MD Metro Area"),
    ("boston-ma", "Boston, MA", "MA", "Boston, MA metro area", "Boston-Cambridge-Newton, MA-NH", "Boston-Cambridge-Newton, MA-NH Metro Area"),
    ("charlotte-nc", "Charlotte, NC", "NC", "Charlotte, NC metro area", "Charlotte-Concord-Gastonia, NC-SC", "Charlotte-Concord-Gastonia, NC-SC Metro Area"),
    ("chicago-il", "Chicago, IL", "IL", "Chicago, IL metro area", "Chicago-Naperville-Elgin, IL-IN-WI", "Chicago-Naperville-Elgin, IL-IN Metro Area"),
    ("cincinnati-oh", "Cincinnati, OH", "OH", "Cincinnati, OH metro area", "Cincinnati, OH-KY-IN", "Cincinnati, OH-KY-IN Metro Area"),
    ("cleveland-oh", "Cleveland, OH", "OH", "Cleveland, OH metro area", "Cleveland-Elyria, OH", "Cleveland, OH Metro Area"),
    ("columbus-oh", "Columbus, OH", "OH", "Columbus, OH metro area", "Columbus, OH", "Columbus, OH Metro Area"),
    ("dallas-tx", "Dallas, TX", "TX", "Dallas, TX metro area", "Dallas-Fort Worth-Arlington, TX", "Dallas-Fort Worth-Arlington, TX Metro Area"),
    ("denver-co", "Denver, CO", "CO", "Denver, CO metro area", "Denver-Aurora-Lakewood, CO", "Denver-Aurora-Centennial, CO Metro Area"),
    ("detroit-mi", "Detroit, MI", "MI", "Detroit, MI metro area", "Detroit-Warren-Dearborn, MI", "Detroit-Warren-Dearborn, MI Metro Area"),
    ("fort-lauderdale-fl", "Fort Lauderdale, FL", "FL", "Fort Lauderdale, FL metro area", None, None),
    ("fort-worth-tx", "Fort Worth, TX", "TX", "Fort Worth, TX metro area", None, None),
    ("houston-tx", "Houston, TX", "TX", "Houston, TX metro area", "Houston-The Woodlands-Sugar Land, TX", "Houston-Pasadena-The Woodlands, TX Metro Area"),
    ("indianapolis-in", "Indianapolis, IN", "IN", "Indianapolis, IN metro area", "Indianapolis-Carmel-Anderson, IN", "Indianapolis-Carmel-Greenwood, IN Metro Area"),
    ("jacksonville-fl", "Jacksonville, FL", "FL", "Jacksonville, FL metro area", "Jacksonville, FL", "Jacksonville, FL Metro Area"),
    ("kansas-city-mo", "Kansas City, MO", "MO", "Kansas City, MO metro area", "Kansas City, MO-KS", "Kansas City, MO-KS Metro Area"),
    ("las-vegas-nv", "Las Vegas, NV", "NV", "Las Vegas, NV metro area", "Las Vegas-Henderson-Paradise, NV", "Las Vegas-Henderson-North Las Vegas, NV Metro Area"),
    ("los-angeles-ca", "Los Angeles, CA", "CA", "Los Angeles, CA metro area", "Los Angeles-Long Beach-Anaheim, CA", "Los Angeles-Long Beach-Anaheim, CA Metro Area"),
    ("miami-fl", "Miami, FL", "FL", "Miami, FL metro area", "Miami-Fort Lauderdale-Pompano Beach, FL", "Miami-Fort Lauderdale-West Palm Beach, FL Metro Area"),
    ("milwaukee-wi", "Milwaukee, WI", "WI", "Milwaukee, WI metro area", "Milwaukee-Waukesha, WI", "Milwaukee-Waukesha, WI Metro Area"),
    ("minneapolis-mn", "Minneapolis, MN", "MN", "Minneapolis, MN metro area", "Minneapolis-St. Paul-Bloomington, MN-WI", "Minneapolis-St. Paul-Bloomington, MN-WI Metro Area"),
    ("montgomery-county-pa", "Montgomery County, PA", "PA", "Montgomery County, PA metro area", None, None),
    ("nashville-tn", "Nashville, TN", "TN", "Nashville, TN metro area", "Nashville-Davidson--Murfreesboro--Franklin, TN", "Nashville-Davidson--Murfreesboro--Franklin, TN Metro Area"),
    ("nassau-county-ny", "Nassau County, NY", "NY", "Nassau County, NY metro area", None, None),
    ("new-brunswick-nj", "New Brunswick, NJ", "NJ", "New Brunswick, NJ metro area", None, None),
    ("new-york-ny", "New York, NY", "NY", "New York, NY metro area", "New York-Newark-Jersey City, NY-NJ-PA", "New York-Newark-Jersey City, NY-NJ Metro Area"),
    ("newark-nj", "Newark, NJ", "NJ", "Newark, NJ metro area", None, None),
    ("oakland-ca", "Oakland, CA", "CA", "Oakland, CA metro area", None, None),
    ("orlando-fl", "Orlando, FL", "FL", "Orlando, FL metro area", "Orlando-Kissimmee-Sanford, FL", "Orlando-Kissimmee-Sanford, FL Metro Area"),
    ("philadelphia-pa", "Philadelphia, PA", "PA", "Philadelphia, PA metro area", "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD", "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD Metro Area"),
    ("phoenix-az", "Phoenix, AZ", "AZ", "Phoenix, AZ metro area", "Phoenix-Mesa-Chandler, AZ", "Phoenix-Mesa-Chandler, AZ Metro Area"),
    ("pittsburgh-pa", "Pittsburgh, PA", "PA", "Pittsburgh, PA metro area", "Pittsburgh, PA", "Pittsburgh, PA Metro Area"),
    ("portland-or", "Portland, OR", "OR", "Portland, OR metro area", "Portland-Vancouver-Hillsboro, OR-WA", "Portland-Vancouver-Hillsboro, OR-WA Metro Area"),
    ("providence-ri", "Providence, RI", "RI", "Providence, RI metro area", "Providence-Warwick, RI-MA", "Providence-Warwick, RI-MA Metro Area"),
    ("riverside-ca", "Riverside, CA", "CA", "Riverside, CA metro area", "Riverside-San Bernardino-Ontario, CA", "Riverside-San Bernardino-Ontario, CA Metro Area"),
    ("sacramento-ca", "Sacramento, CA", "CA", "Sacramento, CA metro area", "Sacramento-Roseville-Folsom, CA", "Sacramento-Roseville-Folsom, CA Metro Area"),
    ("san-antonio-tx", "San Antonio, TX", "TX", "San Antonio, TX metro area", "San Antonio-New Braunfels, TX", "San Antonio-New Braunfels, TX Metro Area"),
    ("san-diego-ca", "San Diego, CA", "CA", "San Diego, CA metro area", "San Diego-Chula Vista-Carlsbad, CA", "San Diego-Chula Vista-Carlsbad, CA Metro Area"),
    ("san-francisco-ca", "San Francisco, CA", "CA", "San Francisco, CA metro area", "San Francisco-Oakland-Berkeley, CA", "San Francisco-Oakland-Fremont, CA Metro Area"),
    ("san-jose-ca", "San Jose, CA", "CA", "San Jose, CA metro area", "San Jose-Sunnyvale-Santa Clara, CA", "San Jose-Sunnyvale-Santa Clara, CA Metro Area"),
    ("seattle-wa", "Seattle, WA", "WA", "Seattle, WA metro area", "Seattle-Tacoma-Bellevue, WA", "Seattle-Tacoma-Bellevue, WA Metro Area"),
    ("st-louis-mo", "St. Louis, MO", "MO", "St. Louis, MO metro area", "St. Louis, MO-IL", "St. Louis, MO-IL Metro Area"),
    ("tampa-fl", "Tampa, FL", "FL", "Tampa, FL metro area", "Tampa-St. Petersburg-Clearwater, FL", "Tampa-St. Petersburg-Clearwater, FL Metro Area"),
    ("virginia-beach-va", "Virginia Beach, VA", "VA", "Virginia Beach, VA metro area", "Virginia Beach-Norfolk-Newport News, VA-NC", "Virginia Beach-Chesapeake-Norfolk, VA-NC Metro Area"),
    ("warren-mi", "Warren, MI", "MI", "Warren, MI metro area", None, None),
    ("washington-dc", "Washington, DC", "DC", "Washington, DC metro area", "Washington-Arlington-Alexandria, DC-VA-MD-WV", "Washington-Arlington-Alexandria, DC-VA-MD-WV Metro Area"),
    ("west-palm-beach-fl", "West Palm Beach, FL", "FL", "West Palm Beach, FL metro area", None, None),
]
