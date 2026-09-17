#!/usr/bin/env python3
"""Run the reproducible, offline website-data build in dependency order."""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PACKAGES = {
    "duckdb": "1.5.4",
    "numpy": "2.5.1",
    "openpyxl": "3.1.5",
    "pandas": "3.0.3",
}


@dataclass(frozen=True)
class Stage:
    name: str
    command: tuple[str, ...]


def required_inputs() -> list[Path]:
    paths = [
        PROJECT_ROOT / "data" / "raw" / "eia_esr" / f"f861{year}.zip"
        for year in range(2013, 2025)
    ]
    paths.extend(
        PROJECT_ROOT / "data" / "raw" / "eia861" / "official" / f"f861{year}.zip"
        for year in range(2013, 2025)
    )
    paths.extend(
        [
            PROJECT_ROOT / "data" / "raw" / "eia_esr" / "pudl_customer_coverage_top10_2013_2024.csv",
            PROJECT_ROOT / "data" / "raw" / "eia_esr" / "pudl_customer_coverage_expanded_2013_2024.csv",
            PROJECT_ROOT / "data" / "raw" / "pudl_eia861_ne_ny_2024_roster.csv",
            PROJECT_ROOT / "data" / "raw" / "eia861" / "pudl_reliability_top10_2013_2024.csv",
            PROJECT_ROOT / "data" / "raw" / "eia923" / "pudl_iso_generation_by_fuel_2013_2024.csv",
            PROJECT_ROOT / "data" / "manual" / "iso_fuel_mix_crosschecks.csv",
            PROJECT_ROOT / "data" / "manual" / "reliability_independent_checks.csv",
            PROJECT_ROOT / "data" / "processed" / "utility_panel_candidates_2024.csv",
        ]
    )
    return paths


def preflight(with_workbook: bool) -> None:
    problems: list[str] = []
    if sys.version_info[:2] != (3, 12):
        problems.append(
            f"Python 3.12 is required; found {sys.version.split()[0]} at {sys.executable}"
        )

    for package, expected in EXPECTED_PACKAGES.items():
        try:
            actual = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            problems.append(f"Missing Python package: {package}=={expected}")
            continue
        if actual != expected:
            problems.append(f"{package} must be {expected}; found {actual}")

    if not shutil.which("node"):
        problems.append("Missing command: node")
    if not (shutil.which("soffice") or shutil.which("libreoffice")):
        problems.append("Missing command: soffice or libreoffice")

    missing = [path.relative_to(PROJECT_ROOT) for path in required_inputs() if not path.is_file()]
    if missing:
        problems.append("Missing required inputs:\n  " + "\n  ".join(map(str, missing)))

    if with_workbook:
        print(
            "Note: --with-workbook additionally requires the optional "
            "@oai/artifact-tool Node package."
        )

    if problems:
        raise SystemExit("Preflight failed:\n- " + "\n- ".join(problems))

    print("Preflight passed: exact Python versions, Node, LibreOffice, and all inputs found.")


def stages(with_workbook: bool, skip_tests: bool) -> list[Stage]:
    python = sys.executable
    roe_command = ("node", "scripts/build_ct_roe_pilot.mjs")
    if with_workbook:
        roe_command += ("--with-workbook",)

    result = [
        Stage("ROE annual tables and source register", roe_command),
        Stage("30-utility price panel", (python, "scripts/build_price_panel.py")),
        Stage("42-utility price panel", (python, "scripts/build_expanded_price_check.py")),
        Stage("ownership-price summary", (python, "scripts/build_ownership_price_summary.py")),
        Stage("price models", (python, "scripts/build_price_models.py")),
        Stage("direct official reliability validation", (python, "scripts/validate_reliability_sources.py")),
        Stage("reliability coverage audit", (python, "scripts/build_reliability_audit.py")),
        Stage("reliability models", (python, "scripts/build_reliability_models.py")),
        Stage("price panel models", (python, "scripts/build_price_panel_models.py")),
        Stage("ISO fuel-mix context", (python, "scripts/build_iso_fuel_mix.py")),
        Stage("matched-state ROE case study", (python, "scripts/build_ct_case_study.py")),
    ]
    if not skip_tests:
        result.append(
            Stage(
                "unit tests",
                (python, "-m", "unittest", "discover", "-s", "tests", "-v"),
            )
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="verify the environment and required inputs without rebuilding",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="rebuild data but do not run the unit-test suite",
    )
    parser.add_argument(
        "--with-workbook",
        action="store_true",
        help="also render the optional ROE XLSX workbook using @oai/artifact-tool",
    )
    args = parser.parse_args()

    preflight(args.with_workbook)
    if args.check_only:
        return

    selected = stages(args.with_workbook, args.skip_tests)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONHASHSEED"] = "0"

    for index, stage in enumerate(selected, start=1):
        print(f"\n[{index}/{len(selected)}] {stage.name}", flush=True)
        subprocess.run(
            stage.command,
            cwd=PROJECT_ROOT,
            env=environment,
            check=True,
        )

    print(f"\nCompleted {len(selected)} stages successfully.")


if __name__ == "__main__":
    main()
