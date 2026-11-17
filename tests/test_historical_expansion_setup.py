import csv
import unittest
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (PROJECT_ROOT / relative_path).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


class HistoricalExpansionSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.coverage = read_csv("data/manual/historical_source_coverage.csv")
        cls.events = read_csv("data/manual/ownership_events.csv")
        cls.lineage = read_csv("data/manual/utility_lineage.csv")

    def test_working_start_year_is_supported_by_core_sources(self) -> None:
        core = [row for row in self.coverage if row["priority"] == "core"]
        recommended = {
            int(row["recommended_start_year"])
            for row in core
            if row["recommended_start_year"]
        }
        self.assertEqual(recommended, {2001})

        source_ids = {row["dataset_id"] for row in core}
        self.assertTrue(
            {
                "eia861_sales_to_ultimate_customers",
                "eia_esr_tables_6_8",
                "pudl_eia861_yearly_sales",
                "eia861_utility_data",
                "manual_primary_ownership_sources",
                "bls_cpi_u",
            }.issubset(source_ids)
        )

    def test_reviewed_events_have_unique_ids_and_valid_timing(self) -> None:
        event_ids = [row["event_id"] for row in self.events]
        self.assertEqual(len(event_ids), len(set(event_ids)))

        for row in self.events:
            closing = date.fromisoformat(row["closing_date"])
            self.assertEqual(int(row["year_end_treatment_year"]), closing.year)
            self.assertEqual(int(row["first_full_treatment_year"]), closing.year + 1)
            self.assertEqual(row["review_status"], "reviewed_phase_3")
            self.assertTrue(row["primary_source_url"].startswith("https://"))

    def test_event_flags_and_ownership_classes_are_explicit(self) -> None:
        allowed_boolean = {"true", "false"}
        allowed_class = {"DOM", "MTC", "COOP", "SOE"}
        flag_fields = (
            "parent_changed",
            "ownership_class_changed",
            "utility_id_changed",
            "service_territory_changed",
            "clean_ownership_change_candidate",
        )
        for row in self.events:
            for field in flag_fields:
                self.assertIn(row[field], allowed_boolean)
            self.assertIn(row["old_ownership_class"], allowed_class)
            self.assertIn(row["new_ownership_class"], allowed_class)

    def test_every_event_has_a_lineage_record(self) -> None:
        lineage_ids = {row["lineage_id"] for row in self.lineage}
        utility_ids = {row["utility_id_eia"] for row in self.lineage}
        for event in self.events:
            self.assertIn(event["lineage_id"], lineage_ids)
            self.assertIn(event["utility_id_eia"], utility_ids)


if __name__ == "__main__":
    unittest.main()
