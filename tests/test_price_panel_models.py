"""Regression and reproducibility checks for the focused price-panel page."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import build_price_panel_models as models  # noqa: E402


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
    "residential": {"MTC": -4.064686, "COOP": -10.866532},
    "commercial": {"MTC": -4.085609, "COOP": -7.061788},
    "industrial": {"MTC": -2.091263, "COOP": -6.641535},
}


class PricePanelModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.analysis = models.build_analysis_table()
        cls.results = models.build_results(cls.analysis)
        cls.main_models = {
            model["customer_class"]: model
            for model in cls.results["main_price_models"]
        }
        cls.saidi_models = {
            (model["customer_class"], model["specification"]): model
            for model in cls.results["saidi_comparison_models"]
        }

    def test_student_t_p_value_matches_known_critical_values(self) -> None:
        self.assertAlmostEqual(models.student_t_two_sided_p_value(1.0, 1), 0.5, places=12)
        self.assertAlmostEqual(
            models.student_t_two_sided_p_value(2.045230, 29),
            0.05,
            places=6,
        )
        self.assertAlmostEqual(
            models.student_t_two_sided_p_value(2.063899, 24),
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
            self.assertNotIn(models.REPORTING_TERM, terms)

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
                self.assertIn(models.REPORTING_TERM, terms)
                self.assertTrue(all(0 <= row["p_value"] <= 1 for row in model["coefficients"]))
            baseline_terms = {row["term"] for row in baseline["coefficients"]}
            saidi_terms = {row["term"] for row in with_saidi["coefficients"]}
            self.assertNotIn("routine_saidi_per_100_minutes", baseline_terms)
            self.assertIn("routine_saidi_per_100_minutes", saidi_terms)

    def test_saidi_is_a_small_uncertain_exploratory_addition(self) -> None:
        diagnostics = self.results["diagnostics"]["ownership_coefficient_changes"]
        for customer_class in models.CUSTOMER_CLASSES:
            for ownership in models.OWNERSHIP_TERMS:
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
        processed = json.loads(models.PROCESSED_RESULTS_OUTPUT.read_text())
        site = json.loads(models.SITE_RESULTS_OUTPUT.read_text())
        self.assertEqual(processed, site)
        self.assertEqual(
            models.PROCESSED_ANALYSIS_OUTPUT.read_text(),
            models.SITE_ANALYSIS_OUTPUT.read_text(),
        )
        javascript = models.SITE_RESULTS_JS_OUTPUT.read_text().strip()
        prefix = "window.NE_NY_PRICE_PANEL_MODEL_RESULTS = "
        self.assertTrue(javascript.startswith(prefix))
        self.assertTrue(javascript.endswith(";"))
        self.assertEqual(json.loads(javascript[len(prefix) : -1]), processed)

    def test_overview_price_summary_matches_model_output(self) -> None:
        overview = (PROJECT_ROOT / "site" / "index.html").read_text()
        coefficients = {
            customer_class: {
                row["term"]: row
                for row in model["coefficients"]
                if row["term"].startswith("ownership_")
            }
            for customer_class, model in self.main_models.items()
        }
        coop_magnitudes = [
            abs(rows["ownership_COOP"]["estimate"])
            for rows in coefficients.values()
        ]
        self.assertEqual(
            f"{min(coop_magnitudes):.2f}–{max(coop_magnitudes):.2f}",
            "6.64–10.87",
        )
        self.assertTrue(
            all(
                rows["ownership_COOP"]["confidence_interval_excludes_zero"]
                for rows in coefficients.values()
            )
        )
        self.assertAlmostEqual(
            abs(coefficients["commercial"]["ownership_MTC"]["estimate"]),
            4.09,
            places=2,
        )
        self.assertTrue(
            coefficients["commercial"]["ownership_MTC"][
                "confidence_interval_excludes_zero"
            ]
        )
        self.assertFalse(
            coefficients["residential"]["ownership_MTC"][
                "confidence_interval_excludes_zero"
            ]
        )
        self.assertFalse(
            coefficients["industrial"]["ownership_MTC"][
                "confidence_interval_excludes_zero"
            ]
        )
        self.assertIn("6.64–10.87 cents per kWh below DOM", overview)
        self.assertIn("Commercial prices are an estimated 4.09 cents", overview)

    def test_price_page_is_separate_focused_and_inspectable(self) -> None:
        overview = (PROJECT_ROOT / "site" / "index.html").read_text()
        page = (PROJECT_ROOT / "site" / "price-model.html").read_text()
        javascript = (PROJECT_ROOT / "site" / "price-model.js").read_text()
        self.assertIn('href="price-model.html"', overview)
        self.assertIn("Ownership and bundled electricity prices", page)
        self.assertIn("A panel follows the same utilities", page)
        self.assertIn("not causal effects", page)
        self.assertIn('id="main-price-results-table"', page)
        self.assertIn('id="saidi-comparison-groups"', page)
        self.assertNotIn("CAIDI", page)
        self.assertNotIn("Reliability as the outcome", page)
        self.assertIn("data/price_panel_model_results.js", page)
        self.assertIn('href="data/price_panel_model_analysis.csv"', page)
        self.assertIn('id="model-data-body"', page)
        self.assertIn("renderAnalysisData", javascript)
        self.assertIn("renderMainPriceResults", javascript)
        self.assertIn("renderSaidiComparison", javascript)
        self.assertIn("model-saidi-group", javascript)
        self.assertIn("Inconclusive: CI includes 0", javascript)
        self.assertIn("None of the SAIDI coefficients is distinguishable from zero", javascript)
        self.assertNotIn("The idea in plain language", page)
        self.assertNotIn("professor", page.lower())
        self.assertNotIn("<svg", page)


if __name__ == "__main__":
    unittest.main()
