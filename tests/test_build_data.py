import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from build_data import build_records, build_regional_records


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

    def test_maps_nstar_id_to_eversource_label(self):
        df = pd.DataFrame(
            [{"utility_id_eia": 54913, "year": 2023, "fuel": "solar", "mwh": 5.0}]
        )
        records = build_records(df)
        self.assertEqual(records[0]["utility"], "Eversource")

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


if __name__ == "__main__":
    unittest.main()
