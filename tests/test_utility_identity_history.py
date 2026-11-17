import csv
import unittest
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (PROJECT_ROOT / relative_path).open(
        newline="", encoding="utf-8"
    ) as source:
        return list(csv.DictReader(source))


class UtilityIdentityHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidates = read_csv(
            "data/processed/expanded_utility_candidates_2024.csv"
        )
        cls.lineage = read_csv("data/manual/utility_lineage.csv")
        cls.aliases = read_csv("data/manual/utility_name_aliases.csv")
        cls.coverage = read_csv(
            "data/processed/utility_identity_coverage_2001_2024.csv"
        )

    def test_all_42_current_utilities_have_reviewed_history(self) -> None:
        expected_panels = {row["panel_id"] for row in self.candidates}
        self.assertEqual({row["panel_id"] for row in self.lineage}, expected_panels)
        self.assertEqual(
            {row["review_status"] for row in self.lineage},
            {"reviewed_phase_2", "reviewed_phase_3"},
        )
        current_ids = {row["utility_id_eia"] for row in self.candidates}
        history_ids = {row["utility_id_eia"] for row in self.lineage}
        self.assertTrue(current_ids.issubset(history_ids))

    def test_annual_coverage_is_complete_without_forcing_unverified_rows(self) -> None:
        self.assertEqual(len(self.coverage), 42 * 24)
        keys = {(row["panel_id"], row["year"]) for row in self.coverage}
        self.assertEqual(len(keys), len(self.coverage))
        self.assertEqual(
            {int(row["year"]) for row in self.coverage}, set(range(2001, 2025))
        )
        self.assertEqual(
            {row["coverage_status"] for row in self.coverage},
            {"matched_current_id", "matched_predecessor_combination"},
        )
        self.assertEqual(
            {row["all_ids_in_utility_file"] for row in self.coverage}, {"True"}
        )
        self.assertEqual(
            {row["all_ids_in_sales_file"] for row in self.coverage}, {"True"}
        )

    def test_nstar_and_unitil_predecessors_are_explicit(self) -> None:
        predecessor_rows = [
            row
            for row in self.coverage
            if row["coverage_status"] == "matched_predecessor_combination"
        ]
        by_panel = Counter(row["panel_id"] for row in predecessor_rows)
        self.assertEqual(by_panel, {"DOM_MA_NSTAR": 6, "DOM_NH_UNITIL": 2})

        nstar = {
            row["matched_utility_ids_eia"]
            for row in predecessor_rows
            if row["panel_id"] == "DOM_MA_NSTAR"
        }
        unitil = {
            row["matched_utility_ids_eia"]
            for row in predecessor_rows
            if row["panel_id"] == "DOM_NH_UNITIL"
        }
        self.assertEqual(nstar, {"1998|2886|4089"})
        self.assertEqual(unitil, {"4148|6077"})

    def test_current_ids_start_in_defensible_annual_files(self) -> None:
        current = {
            row["utility_id_eia"]: row
            for row in self.lineage
            if not row["successor_utility_id_eia"]
        }
        self.assertEqual(current["54913"]["valid_from_year"], "2007")
        self.assertEqual(current["24590"]["valid_from_year"], "2002")
        self.assertEqual(current["54913"]["predecessor_utility_id_eia"], "1998|2886|4089")
        self.assertEqual(current["24590"]["predecessor_utility_id_eia"], "4148|6077")

    def test_absorbed_territory_components_are_flagged_without_forcing_coverage(self) -> None:
        current = {
            row["utility_id_eia"]: row
            for row in self.lineage
            if not row["successor_utility_id_eia"]
        }
        self.assertEqual(current["7601"]["predecessor_utility_id_eia"], "3292")
        self.assertEqual(current["1179"]["predecessor_utility_id_eia"], "11522")
        self.assertEqual(current["19791"]["predecessor_utility_id_eia"], "3611")
        self.assertEqual(
            current["19791"]["customer_base_continuity"],
            "requires_phase_4_fixed_territory_decision",
        )
        citizens = next(
            row for row in self.lineage if row["utility_id_eia"] == "3611"
        )
        self.assertEqual(citizens["valid_to_year"], "2002")
        self.assertEqual(citizens["review_status"], "reviewed_phase_3")

    def test_early_published_name_variants_are_kept_separate_from_lineage(self) -> None:
        published = [
            row
            for row in self.aliases
            if row["alias_type"] == "published_table_name_variant"
        ]
        self.assertEqual(len(published), 15)
        self.assertEqual({row["identity_role"] for row in published}, {"current_id"})
        self.assertEqual(
            {row["review_status"] for row in self.aliases}, {"reviewed_phase_2"}
        )
        names = {row["source_name"] for row in published}
        self.assertTrue(
            {
                "Taunton City of",
                "Fairport Village of",
                "Braintree Electric Light Dept. Town of",
            }.issubset(names)
        )


if __name__ == "__main__":
    unittest.main()
