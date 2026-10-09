from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MarketCommentaryChunk, Metro
from app.schemas import CommentaryChunkOut, CommentaryQuery, MarketCommentaryResult

# How many of a metro's chunks to return per query - enough to give a real
# answer without dumping the whole document. Ranking (not just taking the
# first N) is what makes this worth doing at all.
TOP_N_CHUNKS = 3


def _rank_chunks(chunks: list[MarketCommentaryChunk], topic: str) -> list[MarketCommentaryChunk]:
    """TF-IDF similarity between the topic phrase and each of one metro's
    own chunks - deliberately computed fresh here, in-process, over just
    this one document's handful of chunks, not a precomputed vector index.
    Metro selection already narrowed retrieval to one document before this
    function is ever called, so this is "which section of this report,"
    not open-domain search - a lightweight lexical ranking is the right
    tool for that, not a heavier embedding pipeline. See ROADMAP.md
    Phase 8."""
    if len(chunks) <= TOP_N_CHUNKS:
        return chunks
    texts = [c.chunk_text for c in chunks]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([*texts, topic])
    scores = cosine_similarity(matrix[:-1], matrix[-1]).flatten()
    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    return [chunks[i] for i in _diversify_by_section(ranked, chunks)]


def _diversify_by_section(ranked: list[int], chunks: list[MarketCommentaryChunk]) -> list[int]:
    """Prefers one chunk per distinct section before taking a second from
    any section already picked - a real UX problem this was built to fix,
    not a hypothetical one: a long section (e.g. "Rental Market" spanning
    several pages) can dominate the top of a pure-score ranking, returning
    three near-identical excerpts a reader has no way to tell apart in the
    response. One from each of three different, clearly labeled sections
    is more useful than three from the same one, even when a couple of
    them score slightly lower. Falls back to the next best-scoring chunk
    regardless of section once distinct sections run out, rather than
    returning fewer than TOP_N_CHUNKS when more real content exists."""
    selected: list[int] = []
    seen_sections: set[str] = set()
    for i in ranked:
        if chunks[i].section not in seen_sections:
            selected.append(i)
            seen_sections.add(chunks[i].section)
        if len(selected) == TOP_N_CHUNKS:
            return selected
    for i in ranked:
        if i not in selected:
            selected.append(i)
        if len(selected) == TOP_N_CHUNKS:
            break
    return selected


def run_commentary_query(
    db: Session, query: CommentaryQuery, all_metros: list[Metro]
) -> tuple[MarketCommentaryResult | None, list[str], list[str]]:
    """Returns (commentary, unmatched_metros, no_data_metros) - the same
    two honesty-flag lists run_market_query uses, for the same reasons: an
    unresolved metro name and a resolved metro with zero HUD coverage are
    different, both-real situations, never silently collapsed into one
    generic "nothing found"."""
    from app.nl_query import _resolve_metro  # local import: avoids a circular import with nl_query

    metro = _resolve_metro(query.metro, all_metros)
    if metro is None:
        return None, [query.metro], []

    chunks = list(
        db.execute(
            select(MarketCommentaryChunk).where(MarketCommentaryChunk.metro_id == metro.id)
        ).scalars().all()
    )
    if not chunks:
        return None, [], [metro.canonical_name]

    top_chunks = _rank_chunks(chunks, query.topic)
    result = MarketCommentaryResult(
        metro=metro.canonical_name,
        as_of_date=chunks[0].as_of_date,
        source_file=chunks[0].source_file,
        chunks=[
            CommentaryChunkOut(section=c.section, page_number=c.page_number, text=c.chunk_text)
            for c in top_chunks
        ],
    )
    return result, [], []


def explain_commentary(
    query: CommentaryQuery, commentary: MarketCommentaryResult | None, no_data_metros: list[str]
) -> str:
    if commentary is not None:
        return (
            f"Showing HUD market commentary for {commentary.metro}, "
            f"as of {commentary.as_of_date} (source: {commentary.source_file})."
        )
    if no_data_metros:
        return (
            f"No HUD market commentary available for {no_data_metros[0]} - "
            "this metro isn't in the hand-verified set of CHMA reports this project uses."
        )
    return f"Couldn't find a tracked metro matching: {query.metro}."
