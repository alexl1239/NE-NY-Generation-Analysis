import csv
import math
import unittest
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (PROJECT_ROOT / relative_path).open(
        newline="", encoding="utf-8"
    ) as source:
        return list(csv.DictReader(source))


def number_or_none(value: str) -> float | None:
    return None if value == "" else float(value)


class HistoricalPricePanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.panel = read_csv(
            "data/processed/utility_price_history_2001_2024.csv"
        )
        cls.coverage = read_csv(
            "data/processed/historical_price_coverage_2001_2024.csv"
        )
        cls.territory = read_csv(
            "data/processed/historical_territory_comparison_2001_2024.csv"
        )

    def test_panel_is_complete_and_unique(self) -> None:
        self.assertEqual(len(self.panel), 42 * 24 * 3)
        keys = {
            (row["panel_id"], row["year"], row["customer_class"])
            for row in self.panel
        }
        self.assertEqual(len(keys), len(self.panel))
        self.assertEqual(
            {int(row["year"]) for row in self.panel}, set(range(2001, 2025))
        )
        self.assertEqual(
            {row["customer_class"] for row in self.panel},
            {"residential", "commercial", "industrial"},
        )
        self.assertEqual(
            {row["review_status"] for row in self.panel}, {"reviewed_phase_4"}
        )

    def test_published_records_reconcile_to_detailed_eia(self) -> None:
        reported = [
            row for row in self.panel if int(row["published_row_count"]) > 0
        ]
        self.assertEqual(len(reported), 2903)
        self.assertEqual(
            {row["detail_reconciliation_status"] for row in reported},
            {"match"},
        )
        not_reported = [
            row for row in self.panel if int(row["published_row_count"]) == 0
        ]
        self.assertEqual(len(not_reported), 121)
        for row in not_reported:
            self.assertEqual(
                row["source_status"], "not_reported_zero_bundled_customers"
            )
            self.assertEqual(float(row["bundled_customers"]), 0.0)
            self.assertEqual(row["average_price_cents_kwh"], "")

    def test_existing_2013_2024_panel_is_reproduced(self) -> None:
        overlap = [row for row in self.panel if int(row["year"]) >= 2013]
        self.assertEqual(len(overlap), 42 * 12 * 3)
        self.assertEqual(
            {row["overlap_2013_2024_status"] for row in overlap}, {"match"}
        )
        earlier = [row for row in self.panel if int(row["year"]) < 2013]
        self.assertEqual(
            {row["overlap_2013_2024_status"] for row in earlier},
            {"not_applicable"},
        )

    def test_legal_predecessors_are_combined_without_hiding_the_method(self) -> None:
        combined = [
            row
            for row in self.panel
            if row["source_status"] == "reported_combined_legal_predecessors"
        ]
        self.assertEqual(len(combined), 24)
        self.assertEqual(
            {row["panel_id"] for row in combined},
            {"DOM_MA_NSTAR", "DOM_NH_UNITIL"},
        )
        for row in combined:
            revenue = float(row["bundled_revenue_thousand_usd"])
            sales = float(row["bundled_sales_mwh"])
            price = float(row["average_price_cents_kwh"])
            self.assertTrue(math.isclose(price, revenue / sales * 100, abs_tol=1e-9))

    def test_coverage_reports_earliest_defensible_years(self) -> None:
        self.assertEqual(len(self.coverage), 42)
        self.assertEqual(
            {int(row["earliest_defensible_reported_entity_year"]) for row in self.coverage},
            {2001},
        )
        earliest_residential = Counter(
            int(row["earliest_residential_price_year"]) for row in self.coverage
        )
        self.assertEqual(earliest_residential, {2001: 41, 2015: 1})
        self.assertEqual(
            {
                row["panel_id"]
                for row in self.coverage
                if int(row["earliest_residential_price_year"]) == 2015
            },
            {"COOP_ME_5609"},
        )
        self.assertEqual(
            {int(row["unresolved_positive_bundled_observations"]) for row in self.coverage},
            {0},
        )

    def test_acquired_territory_cases_are_separate_and_explicit(self) -> None:
        self.assertEqual(len(self.territory), 3 * 24 * 3)
        self.assertEqual(
            Counter(row["territory_basis_status"] for row in self.territory),
            {
                "current_entity_includes_acquired_territory": 129,
                "combined_current_and_absorbed_component": 81,
                "absorbed_component_missing_not_forced": 3,
                "partial_acquisition_year_not_forced": 3,
            },
        )
        vec_gap = [
            row
            for row in self.territory
            if row["panel_id"] == "COOP_VT_VEC"
            and int(row["year"]) in {2003, 2004}
        ]
        self.assertEqual(len(vec_gap), 6)
        self.assertTrue(
            all(row["fixed_2024_territory_average_price_cents_kwh"] == "" for row in vec_gap)
        )
        combined = [
            row
            for row in self.territory
            if row["territory_basis_status"]
            == "combined_current_and_absorbed_component"
            and row["fixed_2024_territory_average_price_cents_kwh"]
        ]
        for row in combined:
            revenue = number_or_none(
                row["fixed_2024_territory_revenue_thousand_usd"]
            )
            sales = number_or_none(row["fixed_2024_territory_sales_mwh"])
            price = number_or_none(
                row["fixed_2024_territory_average_price_cents_kwh"]
            )
            self.assertIsNotNone(revenue)
            self.assertIsNotNone(sales)
            self.assertIsNotNone(price)
            self.assertTrue(
                math.isclose(price, revenue / sales * 100, abs_tol=1e-9)
            )

    def test_every_row_preserves_official_source_links(self) -> None:
        for row in [*self.panel, *self.territory]:
            self.assertTrue(row["source_url"].startswith("https://www.eia.gov/"))
            self.assertTrue(
                row["detail_source_url"].startswith("https://www.eia.gov/")
            )


if __name__ == "__main__":
    unittest.main()
