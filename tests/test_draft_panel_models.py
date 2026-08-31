"""Regression and reproducibility checks for the focused price-panel page."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import build_draft_panel_models as draft  # noqa: E402


EXPECTED_MAIN_SAMPLES = {
    "residential": (500, 42),
    "commercial": (500, 42),
    "industrial": (477, 41),
}

EXPECTED_MATCHED_SAMPLES = {
    "residential": (290, 25),
    "commercial": (290, 25),
    "industrial": (279, 25),
}

EXPECTED_MAIN_OWNERSHIP = {
    "residential": {"MTC": -4.123617, "COOP": -10.876141},
    "commercial": {"MTC": -4.119999, "COOP": -7.056981},
    "industrial": {"MTC": -2.160264, "COOP": -6.667873},
}


class DraftPanelModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.analysis = draft.build_analysis_table()
        cls.results = draft.build_results(cls.analysis)
        cls.main_models = {
            model["customer_class"]: model
            for model in cls.results["main_price_models"]
        }
        cls.saidi_models = {
            (model["customer_class"], model["specification"]): model
            for model in cls.results["saidi_comparison_models"]
        }

    def test_student_t_p_value_matches_known_critical_values(self) -> None:
        self.assertAlmostEqual(draft.student_t_two_sided_p_value(1.0, 1), 0.5, places=12)
        self.assertAlmostEqual(
            draft.student_t_two_sided_p_value(2.045230, 29),
            0.05,
            places=6,
        )
        self.assertAlmostEqual(
            draft.student_t_two_sided_p_value(2.063899, 24),
            0.05,
            places=6,
        )

    def test_analysis_table_preserves_the_regional_price_panel(self) -> None:
        self.assertEqual(len(self.analysis), 504)
        self.assertEqual(self.analysis["panel_id"].nunique(), 42)
        self.assertEqual(set(self.analysis["iso_market"]), {"ISO-NE", "NYISO"})
        self.assertEqual(int(self.analysis["year"].min()), 2013)
        self.assertEqual(int(self.analysis["year"].max()), 2024)

    def test_main_models_use_all_available_prices(self) -> None:
        for customer_class, expected in EXPECTED_MAIN_SAMPLES.items():
            model = self.main_models[customer_class]
            self.assertEqual(
                (model["observation_count"], model["utility_cluster_count"]),
                expected,
            )
            self.assertEqual(model["geographic_control"], "state")
            terms = {row["term"] for row in model["coefficients"]}
            self.assertNotIn("routine_saidi_per_100_minutes", terms)
            self.assertNotIn(draft.REPORTING_TERM, terms)

    def test_main_ownership_estimates_match_reviewed_values(self) -> None:
        for customer_class, expected in EXPECTED_MAIN_OWNERSHIP.items():
            coefficients = {
                row["term"]: row
                for row in self.main_models[customer_class]["coefficients"]
            }
            for ownership, estimate in expected.items():
                self.assertAlmostEqual(
                    coefficients[f"ownership_{ownership}"]["estimate"],
                    estimate,
                    places=5,
                )

    def test_saidi_comparison_uses_identical_rows(self) -> None:
        for customer_class, expected in EXPECTED_MATCHED_SAMPLES.items():
            baseline = self.saidi_models[(customer_class, "baseline")]
            with_saidi = self.saidi_models[(customer_class, "saidi")]
            for model in (baseline, with_saidi):
                self.assertEqual(
                    (model["observation_count"], model["utility_cluster_count"]),
                    expected,
                )
                self.assertEqual(model["geographic_control"], "state")
                terms = {row["term"] for row in model["coefficients"]}
                self.assertIn(draft.REPORTING_TERM, terms)
                self.assertTrue(all(0 <= row["p_value"] <= 1 for row in model["coefficients"]))
            baseline_terms = {row["term"] for row in baseline["coefficients"]}
            saidi_terms = {row["term"] for row in with_saidi["coefficients"]}
            self.assertNotIn("routine_saidi_per_100_minutes", baseline_terms)
            self.assertIn("routine_saidi_per_100_minutes", saidi_terms)

    def test_saidi_is_a_small_uncertain_exploratory_addition(self) -> None:
        diagnostics = self.results["diagnostics"]["ownership_coefficient_changes"]
        for customer_class in draft.CUSTOMER_CLASSES:
            for ownership in draft.OWNERSHIP_TERMS:
                change = diagnostics[customer_class][ownership]
                self.assertLess(abs(change["saidi_change_from_baseline"]), 0.65)

            model = self.saidi_models[(customer_class, "saidi")]
            result = next(
                row
                for row in model["coefficients"]
                if row["term"] == "routine_saidi_per_100_minutes"
            )
            self.assertGreater(result["p_value"], 0.05)

    def test_only_requested_price_models_are_published(self) -> None:
        self.assertEqual(len(self.results["main_price_models"]), 3)
        self.assertEqual(len(self.results["saidi_comparison_models"]), 6)
        self.assertNotIn("reliability_outcome_models", self.results)
        self.assertNotIn("decision_checks", self.results)
        self.assertNotIn("price_models", self.results)

    def test_written_site_copies_match_processed_outputs(self) -> None:
        processed = json.loads(draft.PROCESSED_RESULTS_OUTPUT.read_text())
        site = json.loads(draft.SITE_RESULTS_OUTPUT.read_text())
        self.assertEqual(processed, site)
        self.assertEqual(
            draft.PROCESSED_ANALYSIS_OUTPUT.read_text(),
            draft.SITE_ANALYSIS_OUTPUT.read_text(),
        )
        javascript = draft.SITE_RESULTS_JS_OUTPUT.read_text().strip()
        prefix = "window.NE_NY_DRAFT_PANEL_MODEL_RESULTS = "
        self.assertTrue(javascript.startswith(prefix))
        self.assertTrue(javascript.endswith(";"))
        self.assertEqual(json.loads(javascript[len(prefix) : -1]), processed)

    def test_price_page_is_separate_focused_and_inspectable(self) -> None:
        overview = (PROJECT_ROOT / "site" / "index.html").read_text()
        page = (PROJECT_ROOT / "site" / "draft-panel-model.html").read_text()
        javascript = (PROJECT_ROOT / "site" / "draft-panel-model.js").read_text()
        self.assertIn('href="draft-panel-model.html"', overview)
        self.assertIn("Ownership and bundled electricity prices", page)
        self.assertIn("A panel follows the same utilities", page)
        self.assertIn("not causal effects", page)
        self.assertIn('id="main-price-results-table"', page)
        self.assertIn('id="saidi-comparison-table"', page)
        self.assertNotIn("CAIDI", page)
        self.assertNotIn("Reliability as the outcome", page)
        self.assertIn("data/draft_panel_model_results.js", page)
        self.assertIn('href="data/draft_panel_model_analysis.csv"', page)
        self.assertIn('id="draft-data-body"', page)
        self.assertIn("renderAnalysisData", javascript)
        self.assertIn("renderMainPriceResults", javascript)
        self.assertIn("renderSaidiComparison", javascript)
        self.assertNotIn("The idea in plain language", page)
        self.assertNotIn("professor", page.lower())
        self.assertNotIn("<svg", page)


if __name__ == "__main__":
    unittest.main()
