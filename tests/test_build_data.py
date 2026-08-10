import sys
import unittest
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from build_data import (
    build_records,
    build_regional_records,
    build_residential_rate_records,
    build_base_rate_records,
)


class TestBuildRecords(unittest.TestCase):
    def test_computes_share_pct_per_utility_year(self):
        df = pd.DataFrame(
            [
                {"utility_id_eia": 13511, "year": 2020, "fuel": "hydro", "mwh": 75.0},
                {"utility_id_eia": 13511, "year": 2020, "fuel": "oil", "mwh": 25.0},
            ]
        )
        records = build_records(df)
        by_fuel = {r["fuel"]: r for r in records}
        self.assertAlmostEqual(by_fuel["Hydro"]["share_pct"], 75.0)
        self.assertAlmostEqual(by_fuel["Oil"]["share_pct"], 25.0)
        self.assertEqual(by_fuel["Hydro"]["utility"], "NYSEG")
        self.assertEqual(by_fuel["Hydro"]["year"], 2020)

    def test_excludes_non_positive_generation_from_share_calc(self):
        df = pd.DataFrame(
            [
                {"utility_id_eia": 4226, "year": 2022, "fuel": "gas", "mwh": 100.0},
                {"utility_id_eia": 4226, "year": 2022, "fuel": "other", "mwh": -5.0},
            ]
        )
        records = build_records(df)
        fuels = {r["fuel"] for r in records}
        self.assertEqual(fuels, {"Gas"})
        self.assertAlmostEqual(records[0]["share_pct"], 100.0)

    def test_titlecases_and_replaces_underscores_in_fuel_names(self):
        df = pd.DataFrame(
            [{"utility_id_eia": 19497, "year": 2021, "fuel": "waste_heat", "mwh": 10.0}]
        )
        records = build_records(df)
        self.assertEqual(records[0]["fuel"], "Waste Heat")

    def test_maps_nstar_id_to_nstar_electric_label(self):
        df = pd.DataFrame(
            [{"utility_id_eia": 54913, "year": 2023, "fuel": "solar", "mwh": 5.0}]
        )
        records = build_records(df)
        self.assertEqual(records[0]["utility"], "NSTAR Electric")

    def test_includes_total_mwh_denominator(self):
        df = pd.DataFrame(
            [
                {"utility_id_eia": 13511, "year": 2020, "fuel": "hydro", "mwh": 75.0},
                {"utility_id_eia": 13511, "year": 2020, "fuel": "oil", "mwh": 25.0},
            ]
        )
        records = build_records(df)
        for record in records:
            self.assertAlmostEqual(record["total_mwh"], 100.0)


class TestBuildRegionalRecords(unittest.TestCase):
    def test_maps_ba_code_to_region_label_and_computes_share_pct(self):
        df = pd.DataFrame(
            [
                {"balancing_authority_code_eia": "NYIS", "year": 2020, "fuel": "gas", "mwh": 60.0},
                {"balancing_authority_code_eia": "NYIS", "year": 2020, "fuel": "hydro", "mwh": 40.0},
                {"balancing_authority_code_eia": "ISNE", "year": 2020, "fuel": "gas", "mwh": 50.0},
            ]
        )
        records = build_regional_records(df)
        by_region_fuel = {(r["region"], r["fuel"]): r for r in records}
        self.assertAlmostEqual(by_region_fuel[("NYISO", "Gas")]["share_pct"], 60.0)
        self.assertAlmostEqual(by_region_fuel[("NYISO", "Hydro")]["share_pct"], 40.0)
        self.assertAlmostEqual(by_region_fuel[("ISO-NE", "Gas")]["share_pct"], 100.0)

    def test_excludes_non_positive_generation_from_share_calc(self):
        df = pd.DataFrame(
            [
                {"balancing_authority_code_eia": "NYIS", "year": 2022, "fuel": "gas", "mwh": 100.0},
                {"balancing_authority_code_eia": "NYIS", "year": 2022, "fuel": "other", "mwh": -5.0},
            ]
        )
        records = build_regional_records(df)
        fuels = {r["fuel"] for r in records}
        self.assertEqual(fuels, {"Gas"})


class TestBuildResidentialRateRecords(unittest.TestCase):
    def test_computes_cents_per_kwh_from_revenue_and_mwh(self):
        df = pd.DataFrame(
            [{"utility_id_eia": 4226, "year": 2020, "revenue": 3_442_687_000.0, "mwh": 14_179_463.0}]
        )
        records = build_residential_rate_records(df)
        self.assertEqual(records[0]["utility"], "Con Edison")
        self.assertEqual(records[0]["year"], 2020)
        self.assertAlmostEqual(records[0]["cents_per_kwh"], 24.28, places=1)

    def test_maps_all_four_utility_ids(self):
        df = pd.DataFrame(
            [
                {"utility_id_eia": 13511, "year": 2021, "revenue": 100.0, "mwh": 1.0},
                {"utility_id_eia": 54913, "year": 2021, "revenue": 100.0, "mwh": 1.0},
                {"utility_id_eia": 4226, "year": 2021, "revenue": 100.0, "mwh": 1.0},
                {"utility_id_eia": 19497, "year": 2021, "revenue": 100.0, "mwh": 1.0},
            ]
        )
        records = build_residential_rate_records(df)
        utilities = {r["utility"] for r in records}
        self.assertEqual(utilities, {"NYSEG", "NSTAR Electric", "Con Edison", "United Illuminating"})


class TestBuildBaseRateRecords(unittest.TestCase):
    def test_passes_through_rate_fields(self):
        df = pd.DataFrame(
            [
                {
                    "utility_id_eia": 4226,
                    "utility": "Con Edison",
                    "year": 2024,
                    "fixed_customer_charge_usd_month": 19.00,
                    "base_distribution_rate_usd_kwh": 0.15112,
                    "modeled_base_delivery_bill_usd": 124.78,
                }
            ]
        )
        records = build_base_rate_records(df)
        self.assertEqual(records[0]["utility"], "Con Edison")
        self.assertEqual(records[0]["year"], 2024)
        self.assertAlmostEqual(records[0]["modeled_base_delivery_bill_usd"], 124.78)


class TestPublishedBaseRateData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        project_root = Path(__file__).resolve().parent.parent
        with (project_root / "data" / "processed" / "base_rates_2020_2024.csv").open(
            newline=""
        ) as source:
            cls.rate_rows = list(csv.DictReader(source))
        with (project_root / "site" / "data" / "base_rate_sources.csv").open(
            newline=""
        ) as source:
            cls.source_rows = list(csv.DictReader(source))

    def test_every_rate_observation_maps_to_a_documented_source(self):
        registered_ids = {row["source_id"] for row in self.source_rows}
        observation_ids = {row["source_id"] for row in self.rate_rows}
        self.assertEqual(observation_ids, registered_ids)
        self.assertEqual(len(self.rate_rows), 20)
        self.assertEqual(len(self.source_rows), 17)

    def test_source_register_has_auditable_locations(self):
        for row in self.source_rows:
            self.assertTrue(row["document"].strip(), row["source_id"])
            self.assertTrue(row["page_or_tariff_leaf"].strip(), row["source_id"])
            self.assertTrue(row["official_source_url"].startswith("https://"), row["source_id"])
            self.assertTrue(row["audit_note"].strip(), row["source_id"])

    def test_all_modeled_bills_tie_to_the_stated_formula(self):
        for row in self.rate_rows:
            expected = (
                Decimal(row["fixed_customer_charge_usd_month"])
                + Decimal(row["usage_assumption_kwh"])
                * Decimal(row["base_distribution_rate_usd_kwh"])
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            self.assertEqual(
                Decimal(row["modeled_base_delivery_bill_usd"]),
                expected,
                msg=f'{row["utility"]} {row["year"]}',
            )


class TestPublishedChartBundle(unittest.TestCase):
    def test_browser_bundle_matches_published_json_files(self):
        project_root = Path(__file__).resolve().parent.parent
        data_dir = project_root / "site" / "data"
        bundle_text = (data_dir / "chart_data.js").read_text()
        prefix = "window.NE_NY_CHART_DATA = "
        self.assertTrue(bundle_text.startswith(prefix))
        self.assertTrue(bundle_text.endswith(";\n"))
        bundle = json.loads(bundle_text[len(prefix):-2])

        expected_files = {
            "generationRecords": "generation_mix.json",
            "regionalRecords": "regional_grid_mix.json",
            "rateRecords": "residential_rates.json",
            "baseRateRecords": "base_rates.json",
        }
        for key, filename in expected_files.items():
            with (data_dir / filename).open() as source:
                self.assertEqual(bundle[key], json.load(source), key)


if __name__ == "__main__":
    unittest.main()
