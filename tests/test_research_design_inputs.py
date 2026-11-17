import csv
import unittest
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative_path: str) -> list[dict[str, str]]:
    with (PROJECT_ROOT / relative_path).open(
        newline="", encoding="utf-8-sig"
    ) as source:
        return list(csv.DictReader(source))


def year_list(value: str) -> list[int]:
    return [] if value == "" else [int(year) for year in value.split("|")]


class ResearchDesignInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.events = read_csv(
            "data/processed/ownership_research_design_events_2001_2024.csv"
        )
        cls.controls = read_csv(
            "data/processed/ownership_research_design_control_pool_2001_2024.csv"
        )

    def test_event_rows_preserve_phase5_coverage_and_add_phase6_roles(self) -> None:
        self.assertEqual(len(self.events), 27)
        self.assertEqual(
            Counter(row["phase6_window_role"] for row in self.events),
            {
                "primary_4_year_window": 15,
                "sensitivity_2_year_window": 3,
                "excluded_insufficient_price_window": 7,
                "excluded_extremely_thin_customer_base": 2,
            },
        )
        self.assertEqual(
            {row["review_status"] for row in self.events},
            {"reviewed_phase_6"},
        )

    def test_selected_windows_exclude_the_closing_year(self) -> None:
        for row in self.events:
            role = row["phase6_window_role"]
            pre = year_list(row["selected_pre_years"])
            post = year_list(row["selected_post_years"])
            closing = int(row["year_end_treatment_year"])
            first_full = int(row["first_full_treatment_year"])
            if role == "excluded_insufficient_price_window":
                self.assertEqual(pre, [])
                self.assertEqual(post, [])
                continue
            expected = 2 if role == "sensitivity_2_year_window" else 4
            self.assertEqual(len(pre), expected)
            self.assertEqual(len(post), expected)
            self.assertTrue(all(year < closing for year in pre))
            self.assertTrue(all(year >= first_full for year in post))
            self.assertNotIn(closing, pre + post)
            self.assertEqual(first_full, closing + 1)

    def test_extremely_thin_cmp_rows_are_not_promoted_to_primary(self) -> None:
        cmp_rows = [
            row
            for row in self.events
            if row["treated_panel_id"] == "MTC_ME_CMP"
        ]
        by_sector = {row["customer_class"]: row for row in cmp_rows}
        self.assertEqual(
            by_sector["residential"]["phase6_window_role"],
            "excluded_extremely_thin_customer_base",
        )
        self.assertEqual(
            by_sector["commercial"]["phase6_window_role"],
            "excluded_extremely_thin_customer_base",
        )
        self.assertEqual(
            by_sector["industrial"]["phase6_window_role"],
            "excluded_insufficient_price_window",
        )
        self.assertEqual(
            float(
                by_sector["residential"][
                    "treated_min_bundled_customers_selected_years"
                ]
            ),
            27.0,
        )
        self.assertEqual(
            float(
                by_sector["commercial"][
                    "treated_min_bundled_customers_selected_years"
                ]
            ),
            6.0,
        )
        self.assertEqual(by_sector["residential"]["candidate_controls_evaluated"], "0")
        self.assertEqual(by_sector["commercial"]["candidate_controls_evaluated"], "0")

    def test_every_included_event_sector_evaluates_all_42_utilities(self) -> None:
        self.assertEqual(len(self.controls), 18 * 42)
        grouped = Counter(
            (row["event_id"], row["customer_class"]) for row in self.controls
        )
        self.assertEqual(len(grouped), 18)
        self.assertEqual(set(grouped.values()), {42})
        keys = {
            (row["event_id"], row["customer_class"], row["candidate_panel_id"])
            for row in self.controls
        }
        self.assertEqual(len(keys), len(self.controls))

    def test_eligible_controls_meet_every_recorded_rule(self) -> None:
        eligible = [
            row for row in self.controls if row["control_pool_eligible"] == "true"
        ]
        self.assertEqual(len(eligible), 132)
        for row in eligible:
            self.assertEqual(row["affected_by_same_transaction"], "false")
            self.assertEqual(row["ownership_class_constant_through_span"], "true")
            self.assertEqual(
                row["ownership_class_matches_treated_old_class"], "true"
            )
            self.assertEqual(row["parent_owner_constant_through_span"], "true")
            self.assertEqual(row["other_reviewed_event_in_span"], "false")
            self.assertEqual(row["price_complete_for_selected_years"], "true")
            self.assertEqual(row["identity_basis_constant_through_span"], "true")
            self.assertEqual(row["territory_basis_constant_through_span"], "true")
            self.assertEqual(row["candidate_customer_base_screen_status"], "passes")
            self.assertEqual(row["eligibility_reasons"], "")

    def test_geographic_tiers_do_not_hide_cross_market_candidates(self) -> None:
        eligible = [
            row for row in self.controls if row["control_pool_eligible"] == "true"
        ]
        self.assertEqual(
            Counter(row["control_pool_tier"] for row in eligible),
            {
                "tier_1_same_state": 27,
                "tier_2_same_market": 39,
                "tier_3_cross_market": 66,
            },
        )
        for row in eligible:
            if row["control_pool_tier"] == "tier_1_same_state":
                self.assertEqual(row["same_state_as_treated"], "true")
            elif row["control_pool_tier"] == "tier_2_same_market":
                self.assertEqual(row["same_state_as_treated"], "false")
                self.assertEqual(row["same_market_as_treated"], "true")
            else:
                self.assertEqual(row["same_market_as_treated"], "false")

    def test_thin_industrial_control_is_flagged_and_excluded(self) -> None:
        nantucket = next(
            row
            for row in self.controls
            if row["event_id"] == "OWN_2022_RIE_01"
            and row["customer_class"] == "industrial"
            and row["candidate_panel_id"] == "MTC_MA_NANTUCKET"
        )
        self.assertEqual(
            nantucket["candidate_customer_base_screen_status"],
            "fails_extremely_thin",
        )
        self.assertEqual(nantucket["control_pool_eligible"], "false")
        self.assertIn("extremely_thin_customer_base", nantucket["eligibility_reasons"])

    def test_control_pool_was_not_matched_on_price_outcomes(self) -> None:
        fields = set(self.controls[0])
        self.assertFalse(any("average_price" in field for field in fields))
        self.assertFalse(any("price_change" in field for field in fields))
        self.assertEqual(
            {row["review_status"] for row in self.controls},
            {"reviewed_phase_6"},
        )


if __name__ == "__main__":
    unittest.main()
