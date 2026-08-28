"""Checks for the focused 10,000-customer expanded price robustness sample."""

from __future__ import annotations

import json
import sys
import unittest
from collections import Counter
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import build_expanded_price_check as expanded  # noqa: E402


EXPECTED_PRIMARY = {
    "residential": {
        "MTC": (-4.124, -8.567, 0.319, False),
        "COOP": (-10.876, -15.118, -6.634, True),
    },
    "commercial": {
        "MTC": (-4.120, -7.547, -0.693, True),
        "COOP": (-7.057, -10.323, -3.791, True),
    },
    "industrial": {
        "MTC": (-2.160, -6.582, 2.262, False),
        "COOP": (-6.668, -10.263, -3.073, True),
    },
}


class ExpandedPriceCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidates = expanded.load_expanded_candidates()
        cls.panel = pd.read_csv(expanded.PANEL_OUTPUT)
        cls.results = json.loads(expanded.RESULT_OUTPUT.read_text())
        cls.models = {
            (model["customer_class"], model["coverage_rule"]): model
            for model in cls.results["models"]
        }

    def test_predeclared_size_rule_and_group_counts(self) -> None:
        self.assertEqual(len(self.candidates), 42)
        self.assertEqual(
            Counter(row["ownership_2024"] for row in self.candidates),
            Counter({"MTC": 11, "DOM": 8, "COOP": 23}),
        )
        self.assertTrue(
            all(
                int(row["residential_customers_2024"]) >= 10_000
                for row in self.candidates
            )
        )

    def test_panel_preserves_all_candidate_years_and_published_missingness(self) -> None:
        self.assertEqual(len(self.panel), 504)
        self.assertEqual(self.panel["panel_id"].nunique(), 42)
        self.assertTrue((self.panel.groupby("panel_id").size() == 12).all())
        self.assertEqual(
            int(self.panel["residential_average_price_cents_kwh"].notna().sum()),
            500,
        )
        self.assertEqual(
            int(self.panel["commercial_average_price_cents_kwh"].notna().sum()),
            500,
        )
        self.assertEqual(
            int(self.panel["industrial_average_price_cents_kwh"].notna().sum()),
            477,
        )
        coop_labels = set(
            self.panel.loc[
                self.panel["ownership_2024"] == "COOP", "eia_ownership_label"
            ].dropna()
        )
        self.assertEqual(coop_labels, {"Cooperative", "Municipal"})

    def test_primary_results_match_reviewed_values(self) -> None:
        for customer_class, expected_effects in EXPECTED_PRIMARY.items():
            model = self.models[(customer_class, "all_published")]
            effects = {row["ownership"]: row for row in model["ownership_results"]}
            for ownership, expected in expected_effects.items():
                estimate, low, high, excludes_zero = expected
                self.assertAlmostEqual(
                    effects[ownership]["estimate_cents_kwh"], estimate, places=3
                )
                self.assertAlmostEqual(
                    effects[ownership]["confidence_95_low"], low, places=3
                )
                self.assertAlmostEqual(
                    effects[ownership]["confidence_95_high"], high, places=3
                )
                self.assertEqual(
                    effects[ownership]["confidence_interval_excludes_zero"],
                    excludes_zero,
                )

    def test_expansion_keeps_all_six_estimate_directions(self) -> None:
        for customer_class in ("residential", "commercial", "industrial"):
            for coverage_rule in ("all_published", "majority_coverage"):
                model = self.models[(customer_class, coverage_rule)]
                self.assertTrue(
                    all(
                        row["estimate_cents_kwh"] < 0
                        for row in model["ownership_results"]
                    )
                )

    def test_site_result_copies_are_exact(self) -> None:
        processed = json.loads(expanded.RESULT_OUTPUT.read_text())
        site = json.loads(expanded.SITE_RESULT_JSON.read_text())
        self.assertEqual(processed, site)
        text = expanded.SITE_RESULT_JS.read_text().strip()
        prefix = "window.NE_NY_EXPANDED_PRICE_MODEL_RESULTS = "
        self.assertTrue(text.startswith(prefix))
        self.assertEqual(json.loads(text[len(prefix) : -1]), processed)

    def test_website_presents_expansion_as_a_check_not_a_replacement(self) -> None:
        html = (PROJECT_ROOT / "site" / "draft-panel-model.html").read_text()
        javascript = (PROJECT_ROOT / "site" / "draft-panel-model.js").read_text()
        self.assertIn('id="draft-expanded-check"', html)
        self.assertIn("Is the price result limited to 30 selected utilities?", html)
        self.assertIn("expanded_price_models", javascript)
        self.assertIn("cannot test reliability", javascript)


if __name__ == "__main__":
    unittest.main()
