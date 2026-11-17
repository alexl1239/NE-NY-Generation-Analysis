"""Review pre- and post-ownership-change price coverage for Phase 5.

The review uses only ownership-class changes already marked as clean in the
Phase 3 event register. It counts consecutive published-price years before the
closing year and after the first full post-closing year. It does not estimate
an ownership effect.

Run: python3 scripts/build_event_window_review.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVENTS_FILE = PROJECT_ROOT / "data" / "manual" / "ownership_events.csv"
PRICE_FILE = (
    PROJECT_ROOT / "data" / "processed" / "utility_price_history_2001_2024.csv"
)
WINDOW_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ownership_event_window_review_2001_2024.csv"
)
TRANSACTION_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "ownership_transaction_window_summary_2001_2024.csv"
)

YEAR_START = 2001
YEAR_END = 2024
READY_YEARS_EACH_SIDE = 4
LIMITED_YEARS_EACH_SIDE = 2
SECTORS = ("residential", "commercial", "industrial")
REVIEWED_DATE = "2026-11-16"

WINDOW_FIELDS = [
    "event_id",
    "transaction_id",
    "panel_id",
    "utility_id_eia",
    "display_name",
    "state",
    "customer_class",
    "closing_date",
    "year_end_treatment_year",
    "first_full_treatment_year",
    "old_parent_name",
    "new_parent_name",
    "old_ownership_class",
    "new_ownership_class",
    "eligible_pre_period_start_year",
    "eligible_pre_period_end_year",
    "eligible_post_period_start_year",
    "eligible_post_period_end_year",
    "available_pre_years",
    "available_post_years",
    "missing_pre_years",
    "missing_post_years",
    "total_pre_price_years",
    "total_post_price_years",
    "consecutive_pre_price_years",
    "consecutive_post_price_years",
    "max_balanced_window_years_each_side",
    "closing_year_price_available",
    "readiness_status",
    "later_analysis_role",
    "limiting_side",
    "readiness_rule",
    "event_source_url",
    "price_source_url_start",
    "price_source_url_end",
    "review_status",
    "reviewed_date",
    "notes",
]

TRANSACTION_FIELDS = [
    "transaction_id",
    "transaction_label",
    "closing_date",
    "year_end_treatment_year",
    "first_full_treatment_year",
    "affected_panel_ids",
    "affected_utilities",
    "affected_utility_count",
    "utility_sector_rows",
    "ready_rows",
    "limited_rows",
    "insufficient_rows",
    "residential_ready_utilities",
    "residential_limited_utilities",
    "residential_insufficient_utilities",
    "commercial_ready_utilities",
    "commercial_limited_utilities",
    "commercial_insufficient_utilities",
    "industrial_ready_utilities",
    "industrial_limited_utilities",
    "industrial_insufficient_utilities",
    "weakest_consecutive_pre_years",
    "weakest_consecutive_post_years",
    "transaction_readiness",
    "recommended_use",
    "review_status",
    "reviewed_date",
    "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


def pipe_years(years: list[int]) -> str:
    return "|".join(str(year) for year in years)


def consecutive_before(available: set[int], end_year: int) -> int:
    count = 0
    for year in range(end_year, YEAR_START - 1, -1):
        if year not in available:
            break
        count += 1
    return count


def consecutive_after(available: set[int], start_year: int) -> int:
    count = 0
    for year in range(start_year, YEAR_END + 1):
        if year not in available:
            break
        count += 1
    return count


def readiness(pre_years: int, post_years: int) -> tuple[str, str, str, str]:
    if pre_years >= READY_YEARS_EACH_SIDE and post_years >= READY_YEARS_EACH_SIDE:
        return (
            "ready_4plus_each_side",
            "primary_candidate",
            "none",
            "At least four consecutive published-price years before the closing "
            "year and after the first full post-closing year.",
        )
    if pre_years >= LIMITED_YEARS_EACH_SIDE and post_years >= LIMITED_YEARS_EACH_SIDE:
        if pre_years < READY_YEARS_EACH_SIDE and post_years < READY_YEARS_EACH_SIDE:
            limiting = "both"
        elif pre_years < READY_YEARS_EACH_SIDE:
            limiting = "pre"
        else:
            limiting = "post"
        return (
            "limited_2_to_3_one_side",
            "sensitivity_or_descriptive_only",
            limiting,
            "At least two consecutive years exist on both sides, but one side "
            "has fewer than four years.",
        )
    if pre_years < LIMITED_YEARS_EACH_SIDE and post_years < LIMITED_YEARS_EACH_SIDE:
        limiting = "both"
    elif pre_years < LIMITED_YEARS_EACH_SIDE:
        limiting = "pre"
    else:
        limiting = "post"
    return (
        "insufficient_fewer_than_2_one_side",
        "exclude_from_event_study",
        limiting,
        "Fewer than two consecutive published-price years exist on at least "
        "one side of the event.",
    )


def build_window_rows() -> list[dict[str, object]]:
    events = [
        row
        for row in read_csv(EVENTS_FILE)
        if row["clean_ownership_change_candidate"] == "true"
    ]
    if len(events) != 9 or len({row["transaction_id"] for row in events}) != 7:
        raise ValueError("Expected 9 clean utility-event rows and 7 transactions")
    if any(
        row["utility_id_changed"] == "true"
        or row["service_territory_changed"] == "true"
        for row in events
    ):
        raise ValueError("A boundary-changing event entered the clean-event review")

    prices = read_csv(PRICE_FILE)
    expected_prices = 42 * 24 * 3
    if len(prices) != expected_prices:
        raise ValueError(f"Expected {expected_prices} price rows; found {len(prices)}")
    price_lookup = {
        (row["panel_id"], int(row["year"]), row["customer_class"]): row
        for row in prices
    }
    if len(price_lookup) != expected_prices:
        raise ValueError("Historical price panel contains duplicate keys")

    rows: list[dict[str, object]] = []
    for event in events:
        event_year = int(event["year_end_treatment_year"])
        first_full_year = int(event["first_full_treatment_year"])
        pre_eligible = list(range(YEAR_START, event_year))
        post_eligible = list(range(first_full_year, YEAR_END + 1))
        for sector in SECTORS:
            annual = {
                year: price_lookup[(event["panel_id"], year, sector)]
                for year in range(YEAR_START, YEAR_END + 1)
            }
            available = {
                year
                for year, row in annual.items()
                if row["average_price_cents_kwh"] != ""
            }
            available_pre = [year for year in pre_eligible if year in available]
            available_post = [year for year in post_eligible if year in available]
            missing_pre = [year for year in pre_eligible if year not in available]
            missing_post = [year for year in post_eligible if year not in available]
            pre_consecutive = consecutive_before(available, event_year - 1)
            post_consecutive = consecutive_after(available, first_full_year)
            status, role, limiting, rule = readiness(
                pre_consecutive, post_consecutive
            )
            rows.append(
                {
                    "event_id": event["event_id"],
                    "transaction_id": event["transaction_id"],
                    "panel_id": event["panel_id"],
                    "utility_id_eia": event["utility_id_eia"],
                    "display_name": annual[YEAR_END]["display_name"],
                    "state": event["state"],
                    "customer_class": sector,
                    "closing_date": event["closing_date"],
                    "year_end_treatment_year": event_year,
                    "first_full_treatment_year": first_full_year,
                    "old_parent_name": event["old_parent_name"],
                    "new_parent_name": event["new_parent_name"],
                    "old_ownership_class": event["old_ownership_class"],
                    "new_ownership_class": event["new_ownership_class"],
                    "eligible_pre_period_start_year": (
                        pre_eligible[0] if pre_eligible else ""
                    ),
                    "eligible_pre_period_end_year": (
                        pre_eligible[-1] if pre_eligible else ""
                    ),
                    "eligible_post_period_start_year": (
                        post_eligible[0] if post_eligible else ""
                    ),
                    "eligible_post_period_end_year": (
                        post_eligible[-1] if post_eligible else ""
                    ),
                    "available_pre_years": pipe_years(available_pre),
                    "available_post_years": pipe_years(available_post),
                    "missing_pre_years": pipe_years(missing_pre),
                    "missing_post_years": pipe_years(missing_post),
                    "total_pre_price_years": len(available_pre),
                    "total_post_price_years": len(available_post),
                    "consecutive_pre_price_years": pre_consecutive,
                    "consecutive_post_price_years": post_consecutive,
                    "max_balanced_window_years_each_side": min(
                        pre_consecutive, post_consecutive
                    ),
                    "closing_year_price_available": str(
                        event_year in available
                    ).lower(),
                    "readiness_status": status,
                    "later_analysis_role": role,
                    "limiting_side": limiting,
                    "readiness_rule": rule,
                    "event_source_url": event["primary_source_url"],
                    "price_source_url_start": annual[YEAR_START]["source_url"],
                    "price_source_url_end": annual[YEAR_END]["source_url"],
                    "review_status": "reviewed_phase_5",
                    "reviewed_date": REVIEWED_DATE,
                    "notes": (
                        "The closing year is excluded from both sides because it "
                        "contains only part-year exposure to the new owner."
                    ),
                }
            )

    expected_rows = len(events) * len(SECTORS)
    if len(rows) != expected_rows:
        raise ValueError(f"Expected {expected_rows} window rows; created {len(rows)}")
    keys = {
        (row["event_id"], row["customer_class"])
        for row in rows
    }
    if len(keys) != expected_rows:
        raise ValueError("Duplicate event-sector rows found")
    return sorted(
        rows,
        key=lambda row: (
            int(row["year_end_treatment_year"]),
            str(row["transaction_id"]),
            str(row["panel_id"]),
            SECTORS.index(str(row["customer_class"])),
        ),
    )


def transaction_readiness(rows: list[dict[str, object]]) -> tuple[str, str]:
    statuses = [str(row["readiness_status"]) for row in rows]
    ready = sum(status == "ready_4plus_each_side" for status in statuses)
    limited = sum(status == "limited_2_to_3_one_side" for status in statuses)
    insufficient = sum(
        status == "insufficient_fewer_than_2_one_side" for status in statuses
    )
    if ready == len(rows):
        return (
            "ready_all_reviewed_sectors",
            "Retain as a primary candidate for later research-design review.",
        )
    if ready > 0:
        return (
            "ready_for_some_utility_sectors",
            "Use only the utility-sector rows marked ready; keep other rows out "
            "of the primary event-study sample.",
        )
    if limited > 0 and insufficient == 0:
        return (
            "limited_short_window",
            "Keep for sensitivity or descriptive discussion, not the primary "
            "event-study sample.",
        )
    return (
        "not_ready_insufficient_window",
        "Exclude from the event-study sample unless additional pre- or post-event "
        "years become available.",
    )


def build_transaction_rows(
    window_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in window_rows:
        grouped[str(row["transaction_id"])].append(row)

    output: list[dict[str, object]] = []
    for transaction_id, rows in grouped.items():
        first = rows[0]
        panel_ids = sorted({str(row["panel_id"]) for row in rows})
        utilities = sorted({str(row["display_name"]) for row in rows})
        status_counts = defaultdict(int)
        for row in rows:
            status_counts[str(row["readiness_status"])] += 1
        summary_status, recommended_use = transaction_readiness(rows)

        sector_counts: dict[str, dict[str, int]] = {}
        for sector in SECTORS:
            sector_rows = [row for row in rows if row["customer_class"] == sector]
            sector_counts[sector] = {
                "ready": sum(
                    row["readiness_status"] == "ready_4plus_each_side"
                    for row in sector_rows
                ),
                "limited": sum(
                    row["readiness_status"] == "limited_2_to_3_one_side"
                    for row in sector_rows
                ),
                "insufficient": sum(
                    row["readiness_status"]
                    == "insufficient_fewer_than_2_one_side"
                    for row in sector_rows
                ),
            }

        output.append(
            {
                "transaction_id": transaction_id,
                "transaction_label": (
                    f"{first['old_parent_name']} to {first['new_parent_name']}"
                ),
                "closing_date": first["closing_date"],
                "year_end_treatment_year": first["year_end_treatment_year"],
                "first_full_treatment_year": first["first_full_treatment_year"],
                "affected_panel_ids": "|".join(panel_ids),
                "affected_utilities": "|".join(utilities),
                "affected_utility_count": len(panel_ids),
                "utility_sector_rows": len(rows),
                "ready_rows": status_counts["ready_4plus_each_side"],
                "limited_rows": status_counts["limited_2_to_3_one_side"],
                "insufficient_rows": status_counts[
                    "insufficient_fewer_than_2_one_side"
                ],
                "residential_ready_utilities": sector_counts["residential"]["ready"],
                "residential_limited_utilities": sector_counts["residential"]["limited"],
                "residential_insufficient_utilities": sector_counts["residential"]["insufficient"],
                "commercial_ready_utilities": sector_counts["commercial"]["ready"],
                "commercial_limited_utilities": sector_counts["commercial"]["limited"],
                "commercial_insufficient_utilities": sector_counts["commercial"]["insufficient"],
                "industrial_ready_utilities": sector_counts["industrial"]["ready"],
                "industrial_limited_utilities": sector_counts["industrial"]["limited"],
                "industrial_insufficient_utilities": sector_counts["industrial"]["insufficient"],
                "weakest_consecutive_pre_years": min(
                    int(row["consecutive_pre_price_years"]) for row in rows
                ),
                "weakest_consecutive_post_years": min(
                    int(row["consecutive_post_price_years"]) for row in rows
                ),
                "transaction_readiness": summary_status,
                "recommended_use": recommended_use,
                "review_status": "reviewed_phase_5",
                "reviewed_date": REVIEWED_DATE,
                "notes": (
                    "Counts are utility-sector rows. A transaction with mixed "
                    "coverage is not promoted to all-sector readiness."
                ),
            }
        )

    if len(output) != 7:
        raise ValueError(f"Expected 7 transaction rows; created {len(output)}")
    return sorted(
        output,
        key=lambda row: (
            int(row["year_end_treatment_year"]), str(row["transaction_id"])
        ),
    )


def main() -> None:
    window_rows = build_window_rows()
    transaction_rows = build_transaction_rows(window_rows)
    write_csv(WINDOW_OUTPUT, WINDOW_FIELDS, window_rows)
    write_csv(TRANSACTION_OUTPUT, TRANSACTION_FIELDS, transaction_rows)


if __name__ == "__main__":
    main()
