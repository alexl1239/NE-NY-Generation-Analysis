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


def year_list(value: str) -> list[int]:
    return [] if value == "" else [int(year) for year in value.split("|")]


class EventWindowReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.windows = read_csv(
            "data/processed/ownership_event_window_review_2001_2024.csv"
        )
        cls.transactions = read_csv(
            "data/processed/ownership_transaction_window_summary_2001_2024.csv"
        )

    def test_review_covers_all_clean_event_sector_rows(self) -> None:
        self.assertEqual(len(self.windows), 9 * 3)
        self.assertEqual(len(self.transactions), 7)
        keys = {
            (row["event_id"], row["customer_class"])
            for row in self.windows
        }
        self.assertEqual(len(keys), len(self.windows))
        self.assertEqual(
            {row["customer_class"] for row in self.windows},
            {"residential", "commercial", "industrial"},
        )
        self.assertEqual(
            {row["review_status"] for row in self.windows},
            {"reviewed_phase_5"},
        )

    def test_closing_year_is_excluded_from_both_windows(self) -> None:
        for row in self.windows:
            closing_year = int(row["year_end_treatment_year"])
            first_full = int(row["first_full_treatment_year"])
            pre = year_list(row["available_pre_years"])
            post = year_list(row["available_post_years"])
            self.assertTrue(all(year < closing_year for year in pre))
            self.assertTrue(all(year >= first_full for year in post))
            self.assertNotIn(closing_year, pre)
            self.assertNotIn(closing_year, post)
            self.assertEqual(first_full, closing_year + 1)

    def test_readiness_counts_are_reproducible(self) -> None:
        self.assertEqual(
            Counter(row["readiness_status"] for row in self.windows),
            {
                "ready_4plus_each_side": 17,
                "insufficient_fewer_than_2_one_side": 7,
                "limited_2_to_3_one_side": 3,
            },
        )
        for row in self.windows:
            pre = int(row["consecutive_pre_price_years"])
            post = int(row["consecutive_post_price_years"])
            status = row["readiness_status"]
            if status == "ready_4plus_each_side":
                self.assertGreaterEqual(pre, 4)
                self.assertGreaterEqual(post, 4)
                self.assertEqual(row["later_analysis_role"], "primary_candidate")
            elif status == "limited_2_to_3_one_side":
                self.assertGreaterEqual(pre, 2)
                self.assertGreaterEqual(post, 2)
                self.assertTrue(pre < 4 or post < 4)
            else:
                self.assertTrue(pre < 2 or post < 2)
                self.assertEqual(
                    row["later_analysis_role"], "exclude_from_event_study"
                )

    def test_known_event_windows_are_classified_as_expected(self) -> None:
        by_transaction = {
            row["transaction_id"]: row for row in self.transactions
        }
        expected = {
            "TXN_2001_EMERA_BANGOR": (
                0,
                0,
                3,
                "not_ready_insufficient_window",
            ),
            "TXN_2002_GRID_NIMO": (
                0,
                0,
                3,
                "not_ready_insufficient_window",
            ),
            "TXN_2007_GAZMETRO_GMP": (
                3,
                0,
                0,
                "ready_all_reviewed_sectors",
            ),
            "TXN_2008_IBERDROLA_ENERGYEAST": (
                8,
                0,
                1,
                "ready_for_some_utility_sectors",
            ),
            "TXN_2013_FORTIS_CH_ENERGY": (
                3,
                0,
                0,
                "ready_all_reviewed_sectors",
            ),
            "TXN_2015_IBERDROLA_UIL": (
                3,
                0,
                0,
                "ready_all_reviewed_sectors",
            ),
            "TXN_2022_PPL_NARRAGANSETT": (
                0,
                3,
                0,
                "limited_short_window",
            ),
        }
        self.assertEqual(set(by_transaction), set(expected))
        for transaction_id, values in expected.items():
            row = by_transaction[transaction_id]
            ready, limited, insufficient, status = values
            self.assertEqual(int(row["ready_rows"]), ready)
            self.assertEqual(int(row["limited_rows"]), limited)
            self.assertEqual(int(row["insufficient_rows"]), insufficient)
            self.assertEqual(row["transaction_readiness"], status)

    def test_immediate_price_gaps_are_not_skipped(self) -> None:
        cmp_industrial = next(
            row
            for row in self.windows
            if row["transaction_id"] == "TXN_2008_IBERDROLA_ENERGYEAST"
            and row["panel_id"] == "MTC_ME_CMP"
            and row["customer_class"] == "industrial"
        )
        self.assertEqual(int(cmp_industrial["consecutive_pre_price_years"]), 0)
        self.assertEqual(int(cmp_industrial["consecutive_post_price_years"]), 0)
        self.assertEqual(
            cmp_industrial["readiness_status"],
            "insufficient_fewer_than_2_one_side",
        )

    def test_sources_and_review_rules_are_explicit(self) -> None:
        for row in self.windows:
            self.assertTrue(row["event_source_url"].startswith("https://"))
            self.assertTrue(row["price_source_url_start"].startswith("https://"))
            self.assertTrue(row["price_source_url_end"].startswith("https://"))
            self.assertIn("consecutive", row["readiness_rule"].lower())
        self.assertEqual(
            {row["review_status"] for row in self.transactions},
            {"reviewed_phase_5"},
        )


if __name__ == "__main__":
    unittest.main()
