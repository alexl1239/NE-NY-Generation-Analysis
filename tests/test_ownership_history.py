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


class OwnershipHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.events = read_csv("data/manual/ownership_events.csv")
        cls.sources = read_csv("data/manual/ownership_event_sources.csv")
        cls.annual = read_csv(
            "data/processed/utility_ownership_history_2001_2024.csv"
        )

    def test_event_register_separates_rows_from_transactions(self) -> None:
        self.assertEqual(len(self.events), 20)
        self.assertEqual(len({row["event_id"] for row in self.events}), 20)
        self.assertEqual(len({row["transaction_id"] for row in self.events}), 18)
        clean = [
            row
            for row in self.events
            if row["clean_ownership_change_candidate"] == "true"
        ]
        self.assertEqual(len(clean), 9)
        self.assertEqual(len({row["transaction_id"] for row in clean}), 7)
        self.assertEqual(
            Counter(row["new_ownership_class"] for row in clean),
            {"MTC": 8, "DOM": 1},
        )

    def test_nonclean_cases_are_explicit(self) -> None:
        roles = Counter(row["analysis_role"] for row in self.events)
        self.assertEqual(roles["clean_class_change_candidate"], 9)
        self.assertEqual(roles["same_class_parent_change"], 4)
        self.assertEqual(roles["absorbed_predecessor_not_clean"], 3)
        self.assertEqual(roles["identity_or_boundary_change_not_clean"], 4)
        for row in self.events:
            if row["utility_id_changed"] == "true" or row[
                "service_territory_changed"
            ] == "true":
                self.assertEqual(
                    row["clean_ownership_change_candidate"], "false"
                )

    def test_annual_owner_table_is_complete(self) -> None:
        self.assertEqual(len(self.annual), 42 * 24)
        keys = {(row["panel_id"], row["year"]) for row in self.annual}
        self.assertEqual(len(keys), len(self.annual))
        self.assertEqual(
            {int(row["year"]) for row in self.annual}, set(range(2001, 2025))
        )
        self.assertEqual(
            {row["ownership_class"] for row in self.annual},
            {"DOM", "MTC", "COOP"},
        )
        self.assertEqual(
            {row["review_status"] for row in self.annual},
            {"reviewed_phase_3"},
        )

    def test_year_end_ownership_rule_is_applied(self) -> None:
        ownership = {
            (row["panel_id"], int(row["year"])): row["ownership_class"]
            for row in self.annual
        }
        expected = {
            ("MTC_NY_NIMO", 2001): "DOM",
            ("MTC_NY_NIMO", 2002): "MTC",
            ("MTC_VT_GMP", 2006): "DOM",
            ("MTC_VT_GMP", 2007): "MTC",
            ("MTC_NY_NYSEG", 2007): "DOM",
            ("MTC_NY_NYSEG", 2008): "MTC",
            ("MTC_NY_CENTHUD", 2012): "DOM",
            ("MTC_NY_CENTHUD", 2013): "MTC",
            ("MTC_CT_UI", 2014): "DOM",
            ("MTC_CT_UI", 2015): "MTC",
            ("DOM_RI_RIE", 2021): "MTC",
            ("DOM_RI_RIE", 2022): "DOM",
        }
        for key, value in expected.items():
            self.assertEqual(ownership[key], value)

    def test_boundary_changes_are_visible_in_annual_table(self) -> None:
        status = {
            (row["panel_id"], int(row["year"])): row[
                "territory_comparability_status"
            ]
            for row in self.annual
        }
        self.assertEqual(
            status[("MTC_VT_GMP", 2012)], "pre_acquisition_territory"
        )
        self.assertEqual(
            status[("MTC_VT_GMP", 2013)], "current_reported_entity"
        )
        self.assertEqual(
            status[("MTC_ME_VERSANT", 2013)], "pre_acquisition_territory"
        )
        self.assertEqual(
            status[("MTC_ME_VERSANT", 2014)], "current_reported_entity"
        )
        self.assertEqual(
            status[("COOP_VT_VEC", 2003)],
            "pre_major_acquisition_territory",
        )

    def test_every_cited_source_is_registered(self) -> None:
        registered = {row["source_id"] for row in self.sources}
        self.assertEqual(len(registered), len(self.sources))
        for row in [*self.events, *self.annual]:
            self.assertTrue(set(row["source_ids"].split("|")).issubset(registered))
        external = [row for row in self.sources if row["source_url"]]
        self.assertTrue(all(row["source_url"].startswith("https://") for row in external))


if __name__ == "__main__":
    unittest.main()
