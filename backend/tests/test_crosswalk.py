"""Invariant checks on market_crosswalk.py - the hand-reviewed, hand-edited
table joining Redfin/Apartment List/Census's three independent naming
conventions. Nothing here re-verifies the actual names are *correct*
(that was done by hand against the real downloaded files, see
docs/ROADMAP.md Phase 3) - these tests catch the structural mistake a
future hand-edit could introduce: a typo'd duplicate, a metro dropped
from one field but not another, or the two known-gap sets drifting apart.
"""

from app.market_crosswalk import BLS_AREA_CODES, FHFA_HPI_SERIES_IDS, METRO_COORDINATES, METRO_CROSSWALK

# The 10 metro-division metros (Anaheim, Fort Lauderdale, Fort Worth,
# Montgomery County PA, Nassau County NY, New Brunswick NJ, Newark NJ,
# Oakland, Warren, West Palm Beach) - Redfin tracks these individually,
# Apartment List and Census's metro-level tables only publish the larger
# combined metro they belong to.
EXPECTED_GAP_METRO_IDS = {
    "anaheim-ca",
    "fort-lauderdale-fl",
    "fort-worth-tx",
    "montgomery-county-pa",
    "nassau-county-ny",
    "new-brunswick-nj",
    "newark-nj",
    "oakland-ca",
    "warren-mi",
    "west-palm-beach-fl",
}


def test_crosswalk_has_fifty_metros():
    assert len(METRO_CROSSWALK) == 50


def test_every_row_is_a_six_tuple():
    for row in METRO_CROSSWALK:
        assert len(row) == 6, row


def test_metro_ids_are_unique():
    ids = [row[0] for row in METRO_CROSSWALK]
    assert len(ids) == len(set(ids))


def test_canonical_names_are_unique():
    names = [row[1] for row in METRO_CROSSWALK]
    assert len(names) == len(set(names))


def test_redfin_names_are_unique_and_present():
    # Every metro is Redfin-native - this crosswalk exists because of
    # Redfin's coverage, so redfin_name should never be None.
    redfin_names = [row[3] for row in METRO_CROSSWALK]
    assert all(name is not None for name in redfin_names)
    assert len(redfin_names) == len(set(redfin_names))


def test_aptlist_names_are_unique_when_present():
    aptlist_names = [row[4] for row in METRO_CROSSWALK if row[4] is not None]
    assert len(aptlist_names) == len(set(aptlist_names))


def test_census_income_names_are_unique_when_present():
    census_names = [row[5] for row in METRO_CROSSWALK if row[5] is not None]
    assert len(census_names) == len(set(census_names))


def test_gap_metros_are_exactly_the_expected_ten():
    """aptlist_name is None for exactly the 10 known metro-division
    metros - not more (a real regression: some other metro's rent data
    silently went missing) and not fewer (a gap quietly got "fixed" by
    guessing/borrowing a parent metro's name, which is exactly what this
    crosswalk's whole design is meant to prevent)."""
    actual_gap_ids = {row[0] for row in METRO_CROSSWALK if row[4] is None}
    assert actual_gap_ids == EXPECTED_GAP_METRO_IDS


def test_census_income_gap_matches_aptlist_gap_exactly():
    """The rent gap and the income gap are the same 10 metros, by
    construction (Census's metro-level table has the identical "combined
    metro only" limitation as Apartment List). If a future edit adds a
    census_income_name for one of these 10 without also reconsidering the
    rent side (or vice versa), that's worth a human looking at, not a
    silent divergence."""
    aptlist_gap_ids = {row[0] for row in METRO_CROSSWALK if row[4] is None}
    income_gap_ids = {row[0] for row in METRO_CROSSWALK if row[5] is None}
    assert aptlist_gap_ids == income_gap_ids


def test_every_metro_id_is_a_lowercase_slug():
    for row in METRO_CROSSWALK:
        metro_id = row[0]
        assert metro_id == metro_id.lower()
        assert " " not in metro_id


def test_every_canonical_name_has_a_state_suffix_matching_state_field():
    for metro_id, canonical_name, state, *_ in METRO_CROSSWALK:
        assert canonical_name.endswith(f", {state}"), (metro_id, canonical_name, state)


def test_bls_area_codes_cover_every_metro_with_no_gaps():
    """Unlike aptlist_name/census_income_name, BLS's LAUS genuinely
    covers metropolitan divisions (area_type "C") as well as combined
    metros - so, unlike the other two sources, all 50 metros should have
    a real BLS area code, not 40."""
    assert set(BLS_AREA_CODES) == {row[0] for row in METRO_CROSSWALK}


def test_bls_area_codes_are_unique():
    assert len(BLS_AREA_CODES.values()) == len(set(BLS_AREA_CODES.values()))


def test_bls_area_codes_are_fifteen_characters_matching_series_id_format():
    # series_id = "LAU" + area_code + 2-digit measure code - a
    # malformed area code here would silently corrupt every constructed
    # series ID (see fetch_bls_unemployment.py).
    for metro_id, area_code in BLS_AREA_CODES.items():
        assert len(area_code) == 15, (metro_id, area_code)
        assert area_code[:2] in ("MT", "DV"), (metro_id, area_code)


def test_fhfa_hpi_series_ids_are_a_real_subset_not_all_fifty():
    """Unlike BLS, FHFA genuinely doesn't publish one combined index for
    large multi-division metros (LA, Chicago, SF, Seattle, DC, Miami,
    Philadelphia, Dallas, Detroit) - a real, meaningfully different
    coverage gap from every other source. This should stay a real
    subset, not accidentally regress to "all 50" (which would mean
    someone quietly started approximating from a division) or shrink
    further without anyone noticing."""
    ids = set(FHFA_HPI_SERIES_IDS)
    all_metros = {row[0] for row in METRO_CROSSWALK}
    assert ids < all_metros  # strict subset
    assert len(ids) == 38
    for big_metro in ("los-angeles-ca", "chicago-il", "san-francisco-ca", "washington-dc"):
        assert big_metro not in ids


def test_fhfa_hpi_series_ids_are_unique_and_well_formed():
    assert len(FHFA_HPI_SERIES_IDS.values()) == len(set(FHFA_HPI_SERIES_IDS.values()))
    for metro_id, series_id in FHFA_HPI_SERIES_IDS.items():
        assert series_id.startswith("ATNHPIUS") and series_id.endswith("Q"), (metro_id, series_id)


def test_metro_coordinates_cover_every_metro_with_no_gaps():
    """Unlike every other crosswalk in this file, coordinates aren't tied
    to one source's data-availability convention - every metro has a real
    named place (either its own CBSA, or the specific city/place within
    a metro-division gap), so this is the one crosswalk with zero gaps."""
    assert set(METRO_COORDINATES) == {row[0] for row in METRO_CROSSWALK}


def test_metro_coordinates_are_within_continental_us_bounds_or_ak_hi():
    # Loose sanity bounds, not a precision check (that was done by hand
    # against the real Census Gazetteer files) - catches a genuinely
    # malformed entry (swapped lat/long, a stray zero, wrong sign) rather
    # than a real but unusual coordinate.
    for metro_id, (lat, lon) in METRO_COORDINATES.items():
        in_continental_us = 24 <= lat <= 50 and -125 <= lon <= -66
        in_alaska = 51 <= lat <= 72 and -180 <= lon <= -129
        in_hawaii = 18 <= lat <= 23 and -161 <= lon <= -154
        assert in_continental_us or in_alaska or in_hawaii, (metro_id, lat, lon)
