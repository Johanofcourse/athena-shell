"""Runs backend/evals/cases.py against the live DeepSeek-backed NL layer
and scores the result. This is the artifact PRODUCT_REVIEW.md called for:
a repeatable number, not "I tried a few queries and they looked fine."

Run with: python -m evals.run_eval
Costs real (small) DeepSeek API usage - 18 queries at deepseek-flash rates.
"""

from app.database import SessionLocal
from app.nl_query import interpret_query, run_market_query
from evals.cases import CASES


def check_case(db, case: dict) -> tuple[list[str], list[str]]:
    """Returns (passed_checks, failed_checks) as human-readable strings."""
    passed, failed = [], []

    filters = interpret_query(case["query"])

    if "expect_metric" in case:
        ok = filters.metric.value in case["expect_metric"]
        (passed if ok else failed).append(f"metric={filters.metric.value} (expected one of {case['expect_metric']})")

    if "expect_metros_contains" in case:
        metros_lower = [m.lower() for m in filters.metros]
        for city in case["expect_metros_contains"]:
            ok = any(city in m for m in metros_lower)
            (passed if ok else failed).append(f"metros contains '{city}' (got {filters.metros})")

    if case.get("expect_metros_empty"):
        ok = len(filters.metros) == 0
        (passed if ok else failed).append(f"metros empty (got {filters.metros})")

    if "expect_sort_by" in case:
        ok = filters.sort_by == case["expect_sort_by"]
        (passed if ok else failed).append(f"sort_by={filters.sort_by} (expected {case['expect_sort_by']})")

    if "expect_sort_order" in case:
        ok = filters.sort_order == case["expect_sort_order"]
        (passed if ok else failed).append(f"sort_order={filters.sort_order} (expected {case['expect_sort_order']})")

    if "expect_bed_size" in case:
        ok = filters.bed_size == case["expect_bed_size"]
        (passed if ok else failed).append(f"bed_size={filters.bed_size} (expected {case['expect_bed_size']})")

    if "expect_start_period_prefix" in case:
        prefixes = case["expect_start_period_prefix"]
        prefixes = tuple(prefixes) if isinstance(prefixes, list) else (prefixes,)
        ok = bool(filters.start_period) and filters.start_period.startswith(prefixes)
        (passed if ok else failed).append(
            f"start_period={filters.start_period} (expected prefix one of {prefixes})"
        )

    if case.get("expect_unsupported_nonempty"):
        ok = len(filters.unsupported_aspects) > 0
        (passed if ok else failed).append(f"unsupported_aspects={filters.unsupported_aspects}")

    needs_query = case.get("expect_no_data_nonempty") or case.get("expect_unmatched_nonempty")
    if needs_query:
        _, unmatched, no_data = run_market_query(db, filters)
        if case.get("expect_no_data_nonempty"):
            ok = len(no_data) > 0
            (passed if ok else failed).append(f"no_data_metros={no_data}")
        if case.get("expect_unmatched_nonempty"):
            ok = len(unmatched) > 0
            (passed if ok else failed).append(f"unmatched_metros={unmatched}")

    return passed, failed


def check_repeatability(query: str, n: int = 5) -> None:
    """Not a pass/fail check - a documented observation. We already saw by
    hand that the same ambiguous ranking question can pick a different,
    still-defensible metric on different runs. This reports how often that
    actually happens rather than leaving it as a one-off anecdote."""
    metrics_seen = []
    for _ in range(n):
        filters = interpret_query(query)
        metrics_seen.append(filters.metric.value)

    unique = set(metrics_seen)
    print(f'Repeatability check ("{query}"), {n} runs:')
    print(f"  metrics chosen: {metrics_seen}")
    if len(unique) == 1:
        print(f"  -> stable: always picked '{metrics_seen[0]}'")
    else:
        print(f"  -> NOT stable: {len(unique)} different metrics across {n} runs ({unique})")


def main() -> None:
    db = SessionLocal()
    total_checks = 0
    passed_checks = 0
    fully_passed_cases = 0

    try:
        for case in CASES:
            try:
                passed, failed = check_case(db, case)
            except Exception as exc:  # noqa: BLE001 - surface any failure as a failed case, don't crash the run
                print(f"[ERROR] {case['id']}: {exc}")
                continue

            total_checks += len(passed) + len(failed)
            passed_checks += len(passed)
            if not failed:
                fully_passed_cases += 1
                print(f"[PASS] {case['id']}: \"{case['query']}\"")
            else:
                print(f"[FAIL] {case['id']}: \"{case['query']}\"")
                for f in failed:
                    print(f"         ✗ {f}")
                for p in passed:
                    print(f"         ✓ {p}")
    finally:
        db.close()

    print()
    print(f"Cases fully passed: {fully_passed_cases}/{len(CASES)}")
    print(f"Individual checks passed: {passed_checks}/{total_checks}")
    print()
    check_repeatability("Which metros have the biggest price drops right now?")


if __name__ == "__main__":
    main()
