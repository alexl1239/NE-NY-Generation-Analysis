"""Regression checks for the simple ownership-price models."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import build_price_models  # noqa: E402


EXPECTED_PRIMARY = {
    "residential": {
        "counts": (347, 30, 20, 20),
        "MTC": (-7.070180, -13.303100, -0.837261),
        "COOP": (-12.045442, -18.242286, -5.848597),
    },
    "commercial": {
        "counts": (347, 30, 20, 20),
        "MTC": (-6.010784, -9.925252, -2.096315),
        "COOP": (-7.720616, -11.971548, -3.469683),
    },
    "industrial": {
        "counts": (324, 29, 20, 20),
        "MTC": (-2.615589, -7.162687, 1.931508),
        "COOP": (-6.110893, -9.985353, -2.236433),
    },
}


class PriceModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = build_price_models.build_results()
        cls.models = {
            (model["customer_class"], model["coverage_rule"]): model
            for model in cls.results["models"]
        }

    def test_expected_model_structure(self) -> None:
        self.assertEqual(len(self.models), 6)
        self.assertEqual(self.results["reference_ownership"], "DOM")
        self.assertEqual(
            self.results["model"],
            "Unweighted OLS with ownership, state, and year indicators",
        )
        self.assertEqual(self.results["interpretation_limit"], "Associational, not causal")
        self.assertEqual(self.results["cpi_u_annual_2013_100"][2013], 100.0)
        self.assertEqual(self.results["cpi_u_annual_2013_100"][2024], 134.655)

    def test_primary_estimates_match_reviewed_values(self) -> None:
        for customer_class, expected in EXPECTED_PRIMARY.items():
            model = self.models[(customer_class, "all_published")]
            counts = (
                model["observation_count"],
                model["utility_cluster_count"],
                model["parameter_count"],
                model["design_rank"],
            )
            self.assertEqual(counts, expected["counts"])
            effects = {row["ownership"]: row for row in model["ownership_results"]}
            for ownership in ("MTC", "COOP"):
                estimate, low, high = expected[ownership]
                self.assertAlmostEqual(effects[ownership]["estimate_cents_kwh"], estimate, places=5)
                self.assertAlmostEqual(effects[ownership]["confidence_95_low"], low, places=5)
                self.assertAlmostEqual(effects[ownership]["confidence_95_high"], high, places=5)

    def test_plain_language_significance_reading(self) -> None:
        residential = self.models[("residential", "all_published")]
        commercial = self.models[("commercial", "all_published")]
        industrial = self.models[("industrial", "all_published")]
        for model in (residential, commercial):
            self.assertTrue(
                all(row["confidence_interval_excludes_zero"] for row in model["ownership_results"])
            )
        industrial_effects = {
            row["ownership"]: row for row in industrial["ownership_results"]
        }
        self.assertFalse(industrial_effects["MTC"]["confidence_interval_excludes_zero"])
        self.assertTrue(industrial_effects["COOP"]["confidence_interval_excludes_zero"])

    def test_majority_coverage_check_keeps_direction(self) -> None:
        for customer_class in build_price_models.CUSTOMER_CLASSES:
            model = self.models[(customer_class, "majority_coverage")]
            self.assertTrue(
                all(row["estimate_cents_kwh"] < 0 for row in model["ownership_results"])
            )

    def test_written_site_copy_matches_processed_copy(self) -> None:
        processed = json.loads(build_price_models.PROCESSED_OUTPUT.read_text())
        site = json.loads(build_price_models.SITE_JSON_OUTPUT.read_text())
        self.assertEqual(processed, site)
        js_text = build_price_models.SITE_JS_OUTPUT.read_text().strip()
        prefix = "window.NE_NY_OWNERSHIP_PRICE_MODEL_RESULTS = "
        self.assertTrue(js_text.startswith(prefix))
        self.assertTrue(js_text.endswith(";"))
        self.assertEqual(json.loads(js_text[len(prefix) : -1]), processed)

    def test_website_keeps_observed_data_and_links_the_new_draft_page(self) -> None:
        html = (PROJECT_ROOT / "site" / "index.html").read_text()
        draft_html = (PROJECT_ROOT / "site" / "draft-panel-model.html").read_text()
        draft_javascript = (PROJECT_ROOT / "site" / "draft-panel-model.js").read_text()
        self.assertIn('id="observed-comparison-panel"', html)
        self.assertIn('href="draft-panel-model.html"', html)
        self.assertNotIn('id="adjusted-comparison-panel"', html)
        self.assertIn("data/draft_panel_model_results.js", draft_html)
        self.assertIn('id="draft-price-results-table"', draft_html)
        self.assertIn("renderPriceResults", draft_javascript)
        self.assertNotIn("renderOwnershipChart", draft_javascript)


if __name__ == "__main__":
    unittest.main()
