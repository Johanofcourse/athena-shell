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

# A fourth, independent naming/coding convention: BLS's Local Area
# Unemployment Statistics (LAUS) area codes. Unlike the fields above,
# this isn't matched against a downloaded file's column headers - it's
# used to construct BLS API series IDs directly ("LAU" + area_code +
# measure_code), since LAUS data comes from BLS's registered public API,
# not a manually-downloaded file. Kept as a separate dict rather than a
# 7th crosswalk column since the lookup direction and purpose are
# genuinely different from the rest of this file.
#
# Real find matching all 50 metros required: unlike Apartment List and
# Census's income table, BLS's LAUS *does* publish metropolitan
# *divisions* separately (area_type "C") - so all 10 of the metro-
# division metros below have real, non-approximated area codes here,
# not another gap. Matched via data/samples/la.area (BLS's own area
# reference file) using the same first-city-token + state heuristic as
# the other crosswalks, then hand-reviewed; one (New Brunswick, filed by
# BLS under "Lakewood-New Brunswick, NJ") needed a manual match since it
# doesn't start with the expected city token.
BLS_AREA_CODES: dict[str, str] = {
    "anaheim-ca": "DV0611244000000",  # Anaheim-Santa Ana-Irvine, CA
    "atlanta-ga": "MT1312060000000",  # Atlanta-Sandy Springs-Roswell, GA
    "austin-tx": "MT4812420000000",  # Austin-Round Rock-San Marcos, TX
    "baltimore-md": "MT2412580000000",  # Baltimore-Columbia-Towson, MD
    "boston-ma": "MT2514460000000",  # Boston-Cambridge-Newton, MA-NH
    "charlotte-nc": "MT3716740000000",  # Charlotte-Concord-Gastonia, NC-SC
    "chicago-il": "MT1716980000000",  # Chicago-Naperville-Elgin, IL-IN
    "cincinnati-oh": "MT3917140000000",  # Cincinnati, OH-KY-IN
    "cleveland-oh": "MT3917410000000",  # Cleveland, OH
    "columbus-oh": "MT3918140000000",  # Columbus, OH
    "dallas-tx": "MT4819100000000",  # Dallas-Fort Worth-Arlington, TX
    "denver-co": "MT0819740000000",  # Denver-Aurora-Centennial, CO
    "detroit-mi": "MT2619820000000",  # Detroit-Warren-Dearborn, MI
    "fort-lauderdale-fl": "DV1222744000000",  # Fort Lauderdale-Pompano Beach-Sunrise, FL
    "fort-worth-tx": "DV4823104000000",  # Fort Worth-Arlington-Grapevine, TX
    "houston-tx": "MT4826420000000",  # Houston-Pasadena-The Woodlands, TX
    "indianapolis-in": "MT1826900000000",  # Indianapolis-Carmel-Greenwood, IN
    "jacksonville-fl": "MT1227260000000",  # Jacksonville, FL
    "kansas-city-mo": "MT2928140000000",  # Kansas City, MO-KS
    "las-vegas-nv": "MT3229820000000",  # Las Vegas-Henderson-North Las Vegas, NV
    "los-angeles-ca": "MT0631080000000",  # Los Angeles-Long Beach-Anaheim, CA
    "miami-fl": "MT1233100000000",  # Miami-Fort Lauderdale-West Palm Beach, FL
    "milwaukee-wi": "MT5533340000000",  # Milwaukee-Waukesha, WI
    "minneapolis-mn": "MT2733460000000",  # Minneapolis-St. Paul-Bloomington, MN-WI
    "montgomery-county-pa": "DV4233874000000",  # Montgomery County-Bucks County-Chester County, PA
    "nashville-tn": "MT4734980000000",  # Nashville-Davidson--Murfreesboro--Franklin, TN
    "nassau-county-ny": "DV3635004000000",  # Nassau County-Suffolk County, NY
    "new-brunswick-nj": "DV3429484000000",  # Lakewood-New Brunswick, NJ
    "new-york-ny": "MT3635620000000",  # New York-Newark-Jersey City, NY-NJ
    "newark-nj": "DV3435084000000",  # Newark, NJ
    "oakland-ca": "DV0636084000000",  # Oakland-Fremont-Berkeley, CA
    "orlando-fl": "MT1236740000000",  # Orlando-Kissimmee-Sanford, FL
    "philadelphia-pa": "MT4237980000000",  # Philadelphia-Camden-Wilmington, PA-NJ-DE-MD
    "phoenix-az": "MT0438060000000",  # Phoenix-Mesa-Chandler, AZ
    "pittsburgh-pa": "MT4238300000000",  # Pittsburgh, PA
    "portland-or": "MT4138900000000",  # Portland-Vancouver-Hillsboro, OR-WA
    "providence-ri": "MT4439300000000",  # Providence-Warwick, RI-MA
    "riverside-ca": "MT0640140000000",  # Riverside-San Bernardino-Ontario, CA
    "sacramento-ca": "MT0640900000000",  # Sacramento-Roseville-Folsom, CA
    "san-antonio-tx": "MT4841700000000",  # San Antonio-New Braunfels, TX
    "san-diego-ca": "MT0641740000000",  # San Diego-Chula Vista-Carlsbad, CA
    "san-francisco-ca": "MT0641860000000",  # San Francisco-Oakland-Fremont, CA
    "san-jose-ca": "MT0641940000000",  # San Jose-Sunnyvale-Santa Clara, CA
    "seattle-wa": "MT5342660000000",  # Seattle-Tacoma-Bellevue, WA
    "st-louis-mo": "MT2941180000000",  # St. Louis, MO-IL
    "tampa-fl": "MT1245300000000",  # Tampa-St. Petersburg-Clearwater, FL
    "virginia-beach-va": "MT5147260000000",  # Virginia Beach-Chesapeake-Norfolk, VA-NC
    "warren-mi": "DV2647664000000",  # Warren-Troy-Farmington Hills, MI
    "washington-dc": "MT1147900000000",  # Washington-Arlington-Alexandria, DC-VA-MD-WV
    "west-palm-beach-fl": "DV1248424000000",  # West Palm Beach-Boca Raton-Delray Beach, FL
}

# A fifth naming/coding convention: FHFA's House Price Index series IDs
# on FRED (Federal Reserve Economic Data), matched using FRED's own API
# metadata (series titles), the same pattern as BLS_AREA_CODES above -
# not matched against a downloaded file, used to call FRED's API
# directly. Real, meaningfully different coverage gap from every other
# source: FHFA doesn't publish one combined index for large
# multi-division metros at all (Los Angeles, Chicago, San Francisco,
# Seattle, Washington DC, Miami, Philadelphia, Dallas, Detroit) - a
# division's number isn't the combined metro's number, so these are left
# as genuine gaps rather than approximated from one division, same
# reasoning as the metro-division gaps elsewhere in this file. Three of
# the 10 metro-division gap metros (Anaheim, Montgomery County PA, New
# Brunswick) also have no current FHFA division series - discontinued or
# never published. 38/50 real matches.
FHFA_HPI_SERIES_IDS: dict[str, str] = {
    "atlanta-ga": "ATNHPIUS12060Q",  # Atlanta-Sandy Springs-Alpharetta, GA
    "austin-tx": "ATNHPIUS12420Q",  # Austin-Round Rock-Georgetown, TX
    "baltimore-md": "ATNHPIUS12580Q",  # Baltimore-Columbia-Towson, MD
    "boston-ma": "ATNHPIUS14454Q",  # Boston, MA (MSAD)
    "charlotte-nc": "ATNHPIUS16740Q",  # Charlotte-Concord-Gastonia, NC-SC
    "cincinnati-oh": "ATNHPIUS17140Q",  # Cincinnati, OH-KY-IN
    "cleveland-oh": "ATNHPIUS17460Q",  # Cleveland-Elyria, OH
    "columbus-oh": "ATNHPIUS18140Q",  # Columbus, OH
    "denver-co": "ATNHPIUS19740Q",  # Denver-Aurora-Lakewood, CO
    "fort-lauderdale-fl": "ATNHPIUS22744Q",  # Ft. Lauderdale-Pompano Beach-Sunrise, FL
    "fort-worth-tx": "ATNHPIUS23104Q",  # Fort Worth-Arlington-Grapevine, TX
    "houston-tx": "ATNHPIUS26420Q",  # Houston-The Woodlands-Sugar Land, TX
    "indianapolis-in": "ATNHPIUS26900Q",  # Indianapolis-Carmel-Anderson, IN
    "jacksonville-fl": "ATNHPIUS27260Q",  # Jacksonville, FL
    "kansas-city-mo": "ATNHPIUS28140Q",  # Kansas City, MO-KS
    "las-vegas-nv": "ATNHPIUS29820Q",  # Las Vegas-Henderson-Paradise, NV
    "milwaukee-wi": "ATNHPIUS33340Q",  # Milwaukee-Waukesha, WI
    "minneapolis-mn": "ATNHPIUS33460Q",  # Minneapolis-St. Paul-Bloomington, MN-WI
    "nashville-tn": "ATNHPIUS34980Q",  # Nashville-Davidson--Murfreesboro--Franklin, TN
    "nassau-county-ny": "ATNHPIUS35004Q",  # Nassau County-Suffolk County, NY
    "new-york-ny": "ATNHPIUS35614Q",  # New York-Jersey City-White Plains, NY-NJ (MSAD)
    "newark-nj": "ATNHPIUS35084Q",  # Newark, NJ-PA
    "oakland-ca": "ATNHPIUS36084Q",  # Oakland-Berkeley-Livermore, CA
    "orlando-fl": "ATNHPIUS36740Q",  # Orlando-Kissimmee-Sanford, FL
    "phoenix-az": "ATNHPIUS38060Q",  # Phoenix-Mesa-Chandler, AZ
    "pittsburgh-pa": "ATNHPIUS38300Q",  # Pittsburgh, PA
    "portland-or": "ATNHPIUS38900Q",  # Portland-Vancouver-Hillsboro, OR-WA
    "providence-ri": "ATNHPIUS39300Q",  # Providence-Warwick, RI-MA
    "riverside-ca": "ATNHPIUS40140Q",  # Riverside-San Bernardino-Ontario, CA
    "sacramento-ca": "ATNHPIUS40900Q",  # Sacramento-Roseville-Folsom, CA
    "san-antonio-tx": "ATNHPIUS41700Q",  # San Antonio-New Braunfels, TX
    "san-diego-ca": "ATNHPIUS41740Q",  # San Diego-Chula Vista-Carlsbad, CA
    "san-jose-ca": "ATNHPIUS41940Q",  # San Jose-Sunnyvale-Santa Clara, CA
    "st-louis-mo": "ATNHPIUS41180Q",  # St. Louis, MO-IL
    "tampa-fl": "ATNHPIUS45300Q",  # Tampa-St. Petersburg-Clearwater, FL
    "virginia-beach-va": "ATNHPIUS47260Q",  # Virginia Beach-Norfolk-Newport News, VA-NC
    "warren-mi": "ATNHPIUS47644Q",  # Warren-Troy-Farmington Hills, MI
    "west-palm-beach-fl": "ATNHPIUS48424Q",  # West Palm Beach-Boca Raton-Boynton Beach, FL
}

# Metro center coordinates, for map-based browsing (not matched to a
# specific source's own geography convention the way the dicts above
# are - just real coordinates for plotting a point). Sourced from the
# Census Bureau's own Gazetteer files: CBSA centroids (INTPTLAT/
# INTPTLONG) for the 40 combined metros, and the actual named city's
# point (from the Place gazetteer) for the 10 metro-division metros,
# since a division isn't its own CBSA entry. Zero gaps, unlike every
# other crosswalk in this file - a CBSA centroid is a real geometric
# area centroid (not a population-weighted "downtown" point), so a
# large/sprawling metro's dot can land somewhat inland of its named
# city (e.g. Seattle) - that's the data being honest about the area's
# real shape, not an error. Two of the 10 division metros are counties,
# not incorporated cities, so they use a real named place within the
# county instead (Norristown for Montgomery County PA, Hempstead for
# Nassau County NY) rather than a fabricated "county centroid".
METRO_COORDINATES: dict[str, tuple[float, float]] = {
    "anaheim-ca": (33.855502, -117.758657),
    "atlanta-ga": (33.732402, -84.392848),
    "austin-tx": (30.249744, -97.649842),
    "baltimore-md": (39.304361, -76.549501),
    "boston-ma": (42.517606, -71.021993),
    "charlotte-nc": (35.166342, -80.797285),
    "chicago-il": (41.75878, -87.841887),
    "cincinnati-oh": (39.078595, -84.463535),
    "cleveland-oh": (41.667548, -81.43052),
    "columbus-oh": (39.968562, -82.835911),
    "dallas-tx": (32.849171, -96.970489),
    "denver-co": (39.434789, -104.901073),
    "detroit-mi": (42.721848, -83.200846),
    "fort-lauderdale-fl": (26.141227, -80.146731),
    "fort-worth-tx": (32.781954, -97.348573),
    "houston-tx": (29.801005, -95.34262),
    "indianapolis-in": (39.790533, -86.12426),
    "jacksonville-fl": (30.234184, -81.756033),
    "kansas-city-mo": (38.931857, -94.443841),
    "las-vegas-nv": (36.21413, -115.014398),
    "los-angeles-ca": (34.108703, -118.182753),
    "miami-fl": (26.101828, -80.478755),
    "milwaukee-wi": (42.912643, -87.862312),
    "minneapolis-mn": (45.096664, -93.275361),
    "montgomery-county-pa": (40.122076, -75.33987),
    "nashville-tn": (36.091577, -86.72298),
    "nassau-county-ny": (40.704374, -73.619445),
    "new-brunswick-nj": (40.486677, -74.444414),
    "new-york-ny": (40.735425, -73.80773),
    "newark-nj": (40.72422, -74.172574),
    "oakland-ca": (37.769846, -122.22569),
    "orlando-fl": (28.434398, -81.35606),
    "philadelphia-pa": (39.894958, -75.311982),
    "phoenix-az": (33.185765, -112.067862),
    "pittsburgh-pa": (40.471332, -79.863986),
    "portland-or": (45.600622, -122.484378),
    "providence-ri": (41.70684, -71.286687),
    "riverside-ca": (34.538476, -116.134541),
    "sacramento-ca": (38.790272, -121.005643),
    "san-antonio-tx": (29.43306, -98.606973),
    "san-diego-ca": (33.023604, -116.776117),
    "san-francisco-ca": (37.773718, -122.274432),
    "san-jose-ca": (36.908472, -121.371372),
    "seattle-wa": (47.490552, -121.833977),
    "st-louis-mo": (38.740211, -90.345825),
    "tampa-fl": (28.120541, -82.525188),
    "virginia-beach-va": (36.837289, -76.391849),
    "warren-mi": (42.492904, -83.025001),
    "washington-dc": (38.829787, -77.495684),
    "west-palm-beach-fl": (26.745114, -80.127038),
}

# metro_id -> filename under data/samples/hud_chma/, for the
# search_market_commentary tool (Phase 8). A real, honest subset, not all
# 50: a metro only appears here once its HUD CHMA report has actually been
# downloaded and verified to exist (HUD's state listing pages are
# bot-gated, so this is hand-curated, same as every other manually-checked
# source in this project). Most are the most recent full-metro report;
# two deliberate exceptions, both disclosed via as_of_date at query time
# rather than silently included: "los-angeles-ca" is HUD's 2013 report
# (the newest full-LA-metro analysis that exists - newer sub-area reports
# like "Westside" or "San Fernando Valley" only cover part of the metro,
# so weren't used), and "providence-ri" is a statewide report, not a
# metro-specific one (HUD doesn't publish a separate Providence-Warwick
# CHMA - Rhode Island's CHMA covers the whole state).
HUD_CHMA_FILES: dict[str, str] = {
    "anaheim-ca": "AnaheimSantaAnaIrvineCA-CHMA-2022.pdf",
    "austin-tx": "AustinRoundRockTX-CHMA-24.pdf",
    "cincinnati-oh": "CincinnatiOH-KY-IN-CHMA-22.pdf",
    "cleveland-oh": "ClevelandElyriaOH-CHMA-23.pdf",
    "columbus-oh": "ColumbusOH-CHMA-23.pdf",
    "dallas-tx": "DallasPlanoIrvingTX-CHMA-24.pdf",
    "fort-lauderdale-fl": "FortLauderdalePompanoBeachDeerfieldBeachFL-CHMA-22.pdf",
    "fort-worth-tx": "FortWorthArlingtonGrapevineTX-CHMA-25.pdf",
    "houston-tx": "HoustonTheWoodlandsSugarLandTX-CHMA-23.pdf",
    "jacksonville-fl": "JacksonvilleFL-CHMA-24.pdf",
    "los-angeles-ca": "LosAngelesCA_comp_2013.pdf",
    "miami-fl": "MiamiMiamiBeachKendallFL-CHMA-26.pdf",
    "oakland-ca": "OaklandHaywardBerkeleyCA-CHMA-2025.pdf",
    "orlando-fl": "OrlandoKissimmeeSanfordFL-CHMA-24.pdf",
    "providence-ri": "RhodeIsland-CHMA-22.pdf",
    "riverside-ca": "RiversideSanBernardinoOntarioCA-CHMA-2025.pdf",
    "sacramento-ca": "SacramentoRosevilleArdenArcadeCA-CHMA-2022.pdf",
    "san-antonio-tx": "SanAntonioNewBraunfelsTX-CHMA-23.pdf",
    "san-diego-ca": "SanDiegoChulaVistaCarlsbadCA-CHMA-2024.pdf",
    "san-francisco-ca": "SanFranciscoRedwoodCitySouthSanFranciscoCA-CHMA-2024.pdf",
    "san-jose-ca": "SanJoseSunnyvaleSantaClaraCA-CHMA-2024.pdf",
    "tampa-fl": "TampaStPetersburgClearwaterFL-CHMA-24.pdf",
    "west-palm-beach-fl": "WestPalmBeachBocaRatonDelrayBeachFL-CHMA-25.pdf",
}
