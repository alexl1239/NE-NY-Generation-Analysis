import csv
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = PROJECT_ROOT / "data" / "processed" / "historical_schema_pilot.csv"
PRICE_PATH = (
    PROJECT_ROOT / "data" / "processed" / "historical_price_schema_pilot.csv"
)
PILOT_YEARS = {2001, 2002, 2003, 2012, 2013}
SECTORS = {"residential", "commercial", "industrial"}


class HistoricalSchemaPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with SCHEMA_PATH.open(newline="") as source:
            cls.schema_rows = list(csv.DictReader(source))
        with PRICE_PATH.open(newline="") as source:
            cls.price_rows = list(csv.DictReader(source))

    def test_pilot_has_complete_representative_year_grid(self):
        self.assertEqual(len(self.schema_rows), 25)
        self.assertEqual(len(self.price_rows), 630)
        self.assertEqual(
            {int(row["year"]) for row in self.schema_rows}, PILOT_YEARS
        )
        self.assertEqual(
            {int(row["year"]) for row in self.price_rows}, PILOT_YEARS
        )
        self.assertEqual(
            {row["customer_class"] for row in self.price_rows}, SECTORS
        )
        keys = {
            (
                row["panel_id"],
                int(row["year"]),
                row["customer_class"],
            )
            for row in self.price_rows
        }
        self.assertEqual(len(keys), len(self.price_rows))

    def test_published_table_mapping_and_state_modes_are_explicit(self):
        published = [
            row
            for row in self.schema_rows
            if row["source_family"] == "eia_esr_published_tables"
        ]
        self.assertEqual(len(published), 15)
        table_by_sector = {
            "residential": 14,
            "commercial": 15,
            "industrial": 16,
        }
        modern_by_sector = {
            "residential": 6,
            "commercial": 7,
            "industrial": 8,
        }
        for row in published:
            year = int(row["year"])
            expected = (
                table_by_sector[row["customer_class"]]
                if year <= 2003
                else modern_by_sector[row["customer_class"]]
            )
            self.assertEqual(int(row["published_table_number"]), expected)
            self.assertEqual(row["utility_id_available"], "False")
            self.assertEqual(row["parser_status"], "pass")
        early = [row for row in published if int(row["year"]) <= 2002]
        self.assertEqual(
            {row["state_field_mode"] for row in early}, {"state name marker rows"}
        )

    def test_detailed_files_preserve_ids_services_and_sector_break(self):
        sales = [
            row
            for row in self.schema_rows
            if row["source_role"] == "sales to ultimate customers"
        ]
        self.assertEqual(len(sales), 5)
        for row in sales:
            self.assertEqual(row["utility_id_available"], "True")
            self.assertEqual(
                row["service_type_values"], "bundled;delivery;energy"
            )
            expected_fourth = "other" if int(row["year"]) <= 2002 else "transportation"
            self.assertEqual(row["fourth_sector_label"], expected_fourth)

        utility = [
            row
            for row in self.schema_rows
            if row["source_role"] == "utility identity"
        ]
        for row in utility:
            expected = int(row["year"]) >= 2012
            self.assertEqual(row["iso_rto_fields_available"], str(expected))

    def test_2013_overlap_exactly_reproduces_current_panel(self):
        overlap = [row for row in self.price_rows if int(row["year"]) == 2013]
        self.assertEqual(len(overlap), 126)
        self.assertEqual(
            {row["current_2013_overlap_status"] for row in overlap}, {"match"}
        )

    def test_every_matched_published_row_reconciles_to_detailed_eia861(self):
        matched = [
            row for row in self.price_rows if row["esr_match_status"] == "matched"
        ]
        self.assertTrue(matched)
        self.assertEqual(
            {row["detail_reconciliation_status"] for row in matched}, {"match"}
        )

    def test_name_alias_and_lineage_reviews_are_separate(self):
        rows_2001 = [row for row in self.price_rows if int(row["year"]) == 2001]
        alias_ids = {
            row["utility_id_eia"]
            for row in rows_2001
            if row["name_alias_review_needed"] == "True"
        }
        lineage_ids = {
            row["utility_id_eia"]
            for row in rows_2001
            if row["lineage_review_needed"] == "True"
        }
        self.assertEqual(len(alias_ids), 14)
        self.assertEqual(lineage_ids, {"24590", "54913"})


if __name__ == "__main__":
    unittest.main()
