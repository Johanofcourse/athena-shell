"""Tests for market_commentary.py's deterministic retrieval logic - the
search_market_commentary tool's "why" counterpart to test_query_logic.py's
coverage of query_market_metrics. interpret_query's live tool-choice
behavior (does the model actually pick this tool for a "why" question) is
an LLM call, out of scope here the same way POST /query itself is - see
the eval suite for that. What's tested here is what happens once a
CommentaryQuery already exists: metro resolution, the no-coverage case,
and whether ranking actually discriminates by topic rather than just
returning the first few chunks."""

from app.market_commentary import TOP_N_CHUNKS, explain_commentary, run_commentary_query
from app.models import MarketCommentaryChunk, Metro
from app.schemas import CommentaryQuery


def _add_chunk(db, metro_id, section, text, as_of="January 1, 2024", source_file="Testville-CHMA-24.pdf", page=0):
    db.add(
        MarketCommentaryChunk(
            metro_id=metro_id,
            source_file=source_file,
            as_of_date=as_of,
            section=section,
            page_number=page,
            chunk_text=text,
        )
    )


def test_run_commentary_query_unresolved_metro(seeded_db):
    all_metros = seeded_db.query(Metro).all()
    query = CommentaryQuery(metro="Nowhereville", topic="anything")
    commentary, unmatched, no_data = run_commentary_query(seeded_db, query, all_metros)
    assert commentary is None
    assert unmatched == ["Nowhereville"]
    assert no_data == []


def test_run_commentary_query_metro_with_no_chunks(seeded_db):
    # testville-ts resolves fine (it's a real tracked metro) but has no
    # MarketCommentaryChunk rows - a real, distinct case from an
    # unresolved name, same reasoning as no_data_metros vs unmatched_metros
    # on the metrics side.
    all_metros = seeded_db.query(Metro).all()
    query = CommentaryQuery(metro="Testville", topic="anything")
    commentary, unmatched, no_data = run_commentary_query(seeded_db, query, all_metros)
    assert commentary is None
    assert unmatched == []
    assert no_data == ["Testville, TS"]


def test_run_commentary_query_returns_result_with_real_metadata(seeded_db):
    _add_chunk(seeded_db, "testville-ts", "Economic Conditions", "Jobs grew steadily this year.")
    seeded_db.commit()

    all_metros = seeded_db.query(Metro).all()
    query = CommentaryQuery(metro="Testville", topic="jobs")
    commentary, unmatched, no_data = run_commentary_query(seeded_db, query, all_metros)

    assert unmatched == []
    assert no_data == []
    assert commentary is not None
    assert commentary.metro == "Testville, TS"
    assert commentary.as_of_date == "January 1, 2024"
    assert commentary.source_file == "Testville-CHMA-24.pdf"
    assert len(commentary.chunks) == 1
    assert commentary.chunks[0].section == "Economic Conditions"
    assert commentary.chunks[0].text == "Jobs grew steadily this year."


def test_ranking_actually_discriminates_by_topic(seeded_db):
    # Six chunks, only two genuinely about employment - if ranking were a
    # no-op (e.g. just returning the first TOP_N_CHUNKS), this would fail,
    # since the employment-relevant chunks are placed in the middle.
    _add_chunk(seeded_db, "testville-ts", "Population", "Population grew due to net migration inflows.", page=0)
    _add_chunk(seeded_db, "testville-ts", "Population", "Household formation increased among younger residents.", page=1)
    _add_chunk(seeded_db, "testville-ts", "Economic Conditions", "Employment in manufacturing jobs rose sharply this year as factories expanded hiring.", page=2)
    _add_chunk(seeded_db, "testville-ts", "Economic Conditions", "The unemployment rate fell as local employers added jobs across several sectors.", page=3)
    _add_chunk(seeded_db, "testville-ts", "Home Sales Market", "Home sale prices increased amid tight for-sale inventory.", page=4)
    _add_chunk(seeded_db, "testville-ts", "Rental Market", "Apartment vacancy rates declined as rental demand increased.", page=5)
    seeded_db.commit()

    all_metros = seeded_db.query(Metro).all()
    query = CommentaryQuery(metro="Testville", topic="employment and jobs")
    commentary, _, _ = run_commentary_query(seeded_db, query, all_metros)

    assert commentary is not None
    assert len(commentary.chunks) == TOP_N_CHUNKS
    returned_sections = {c.section for c in commentary.chunks}
    assert "Economic Conditions" in returned_sections
    returned_texts = " ".join(c.text for c in commentary.chunks)
    assert "jobs" in returned_texts.lower() or "employ" in returned_texts.lower()


def test_ranking_prefers_distinct_sections_over_more_of_the_same(seeded_db):
    # Real bug this fixes: a long section with several pages all mentioning
    # "rent" can out-score every other section on a rent-related topic,
    # returning three near-identical excerpts a reader can't tell apart.
    # Four Rental Market pages, all genuinely about rent, versus one page
    # each in two other sections that only mention rent in passing - a
    # pure-score ranking would return three Rental Market chunks here.
    for i in range(4):
        _add_chunk(
            seeded_db, "testville-ts", "Rental Market",
            f"Average rent increased this quarter as vacancy tightened across the submarket, page {i}.",
            page=i,
        )
    _add_chunk(seeded_db, "testville-ts", "Economic Conditions", "Employment grew while rent remained a minor factor.", page=10)
    _add_chunk(seeded_db, "testville-ts", "Population", "Population grew; rent was not a major driver.", page=11)
    seeded_db.commit()

    all_metros = seeded_db.query(Metro).all()
    query = CommentaryQuery(metro="Testville", topic="rent")
    commentary, _, _ = run_commentary_query(seeded_db, query, all_metros)

    assert commentary is not None
    returned_sections = [c.section for c in commentary.chunks]
    assert len(returned_sections) == len(set(returned_sections)), (
        f"expected 3 distinct sections, got {returned_sections}"
    )


def test_run_commentary_query_respects_top_n_limit(seeded_db):
    for i in range(TOP_N_CHUNKS + 4):
        _add_chunk(seeded_db, "testville-ts", f"Section {i}", f"Some real estate market text number {i}.", page=i)
    seeded_db.commit()

    all_metros = seeded_db.query(Metro).all()
    query = CommentaryQuery(metro="Testville", topic="market")
    commentary, _, _ = run_commentary_query(seeded_db, query, all_metros)

    assert commentary is not None
    assert len(commentary.chunks) == TOP_N_CHUNKS


def test_explain_commentary_found():
    from app.schemas import CommentaryChunkOut, MarketCommentaryResult

    result = MarketCommentaryResult(
        metro="Testville, TS",
        as_of_date="January 1, 2024",
        source_file="Testville-CHMA-24.pdf",
        chunks=[CommentaryChunkOut(section="Economic Conditions", page_number=0, text="...")],
    )
    text = explain_commentary(CommentaryQuery(metro="Testville", topic="jobs"), result, [])
    assert "Testville, TS" in text
    assert "January 1, 2024" in text
    assert "Testville-CHMA-24.pdf" in text


def test_explain_commentary_no_data():
    text = explain_commentary(CommentaryQuery(metro="Testville", topic="jobs"), None, ["Testville, TS"])
    assert "No HUD market commentary available for Testville, TS" in text


def test_explain_commentary_unmatched():
    text = explain_commentary(CommentaryQuery(metro="Nowhereville", topic="jobs"), None, [])
    assert "Nowhereville" in text
    assert "Couldn't find" in text
