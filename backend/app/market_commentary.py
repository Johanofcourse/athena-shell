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
    return [chunks[i] for i in ranked[:TOP_N_CHUNKS]]


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
        chunks=[CommentaryChunkOut(section=c.section, text=c.chunk_text) for c in top_chunks],
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
