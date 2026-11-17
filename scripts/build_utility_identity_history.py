"""Build the reviewed utility-identity history for the 2001-2024 expansion.

This phase connects the 42 utilities in the current project roster to the names
and EIA utility IDs used in earlier Form EIA-861 files. It does not build prices
or change the website.

Run: python3 scripts/build_utility_identity_history.py
"""

from __future__ import annotations

import csv
import re
import shutil
import subprocess
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_OFFICIAL_DIR = PROJECT_ROOT / "data" / "raw" / "eia861" / "official"
RAW_REFORMATTED_DIR = (
    PROJECT_ROOT / "data" / "raw" / "eia861" / "reformatted"
)
CANDIDATES_FILE = (
    PROJECT_ROOT / "data" / "processed" / "expanded_utility_candidates_2024.csv"
)
LINEAGE_OUTPUT = PROJECT_ROOT / "data" / "manual" / "utility_lineage.csv"
ALIASES_OUTPUT = PROJECT_ROOT / "data" / "manual" / "utility_name_aliases.csv"
COVERAGE_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "utility_identity_coverage_2001_2024.csv"
)

YEAR_START = 2001
YEAR_END = 2024
EIA_SOURCE_PAGE = "https://www.eia.gov/electricity/data/eia861/"

NSTAR_SOURCE = (
    "https://www.sec.gov/Archives/edgar/data/13372/"
    "000001337207000011/nstarelectric8kexh991.htm"
)
UNITIL_SOURCE = (
    "https://investors.unitil.com/news-releases/news-release-details/"
    "unitil-subsidiaries-complete-merger-and-implement-new-rates"
)
CVPS_SOURCE = (
    "https://www.sec.gov/Archives/edgar/data/18808/"
    "000110465912046261/a12-15432_38k.htm"
)
MPS_SOURCE = (
    "https://www.sec.gov/Archives/edgar/data/1127248/"
    "000119312516616784/d155277dex43.htm"
)
VEC_SOURCE = "https://vermontelectric.coop/history"

# The values below are reviewed connections between the current project entity
# and the earlier legal utilities that served the same customers. Canal Electric
# is not included in NSTAR's retail predecessor set because it was wholesale.
PREDECESSORS = {
    54913: (
        {
            "utility_id_eia": 1998,
            "utility_name_eia": "Boston Edison Co",
            "valid_from_year": 2001,
            "valid_to_year": 2006,
            "source_url": NSTAR_SOURCE,
        },
        {
            "utility_id_eia": 2886,
            "utility_name_eia": "Cambridge Electric Light Co",
            "valid_from_year": 2001,
            "valid_to_year": 2006,
            "source_url": NSTAR_SOURCE,
        },
        {
            "utility_id_eia": 4089,
            "utility_name_eia": "Commonwealth Electric Co",
            "valid_from_year": 2001,
            "valid_to_year": 2006,
            "source_url": NSTAR_SOURCE,
        },
    ),
    24590: (
        {
            "utility_id_eia": 4148,
            "utility_name_eia": "Concord Electric Co",
            "valid_from_year": 2001,
            "valid_to_year": 2002,
            "source_url": UNITIL_SOURCE,
        },
        {
            "utility_id_eia": 6077,
            "utility_name_eia": "Exeter & Hampton Electric Co",
            "valid_from_year": 2001,
            "valid_to_year": 2002,
            "source_url": UNITIL_SOURCE,
        },
    ),
}

# Phase 3 found three material territory expansions that are different from
# the NSTAR and Unitil legal-identity replacements above. The current EIA ID
# existed before each acquisition, so these older utilities are recorded as
# absorbed territory components rather than substituted into annual coverage.
# Phase 4 will decide whether to aggregate them when constructing a fixed-
# territory price series. Citizens' Vermont record is absent from the 2003
# reformatted annual file, so its reviewed EIA interval stops in 2002 rather
# than forcing a connection that the published file does not support.
ABSORBED_COMPONENTS = {
    7601: (
        {
            "utility_id_eia": 3292,
            "utility_name_eia": "Central Vermont Pub Serv Corp",
            "valid_from_year": 2001,
            "valid_to_year": 2012,
            "source_url": CVPS_SOURCE,
        },
    ),
    1179: (
        {
            "utility_id_eia": 11522,
            "utility_name_eia": "Maine Public Service Co",
            "valid_from_year": 2001,
            "valid_to_year": 2013,
            "source_url": MPS_SOURCE,
        },
    ),
    19791: (
        {
            "utility_id_eia": 3611,
            "utility_name_eia": "Citizens Communications Co",
            "valid_from_year": 2001,
            "valid_to_year": 2002,
            "source_url": VEC_SOURCE,
        },
    ),
}

# Retail sales remain under Unitil's two predecessor IDs for the full 2002
# annual file even though the merger completed in December 2002.
PREDECESSOR_REPORTING_END = {54913: 2006, 24590: 2002}

CURRENT_SOURCE_OVERRIDES = {
    54913: NSTAR_SOURCE,
    24590: UNITIL_SOURCE,
    3249: (
        "https://www.sec.gov/Archives/edgar/data/1061393/"
        "000119312513274933/d561415dex991.htm"
    ),
    19497: (
        "https://www.sec.gov/Archives/edgar/data/1634997/"
        "000119312515407879/d105528d8k.htm"
    ),
    1179: (
        "https://assets.enmax.com/api/public/content/"
        "7b03872560f14aec86eeae105caee82b?v=19f3e57d"
    ),
    13214: (
        "https://investors.pplweb.com/2022-05-25-PPL-Corporation-completes-"
        "acquisition-of-Rhode-Islands-primary-electric-and-natural-gas-utility"
    ),
}

# These are exact names in the early published price tables. They are spelling
# and word-order variants, not different utilities.
PUBLISHED_NAME_VARIANTS = (
    (2001, 18488, "Taunton City of"),
    (2001, 3477, "Chicopee City of"),
    (2001, 14605, "Peabody City of"),
    (2001, 13831, "Norwich City of"),
    (2001, 5930, "Fairport Village of"),
    (2001, 20481, "Westfield City of"),
    (2001, 17127, "Shrewsbury Town of"),
    (2001, 12473, "Middleborough Town of"),
    (2001, 2144, "Braintree Electric Light Dept. Town of"),
    (2001, 13839, "Norwood City of"),
    (2001, 6775, "Freeport Village of"),
    (2001, 13679, "North Attleborough Town of"),
    (2001, 5480, "Danvers Town of"),
    (2001, 8973, "Hudson Town of"),
    (2002, 18488, "Taunton City of"),
)

LINEAGE_FIELDS = [
    "lineage_record_id",
    "lineage_id",
    "panel_id",
    "utility_id_eia",
    "utility_name_eia",
    "display_name",
    "state",
    "valid_from_year",
    "valid_to_year",
    "predecessor_utility_id_eia",
    "successor_utility_id_eia",
    "name_aliases",
    "service_territory_continuity",
    "customer_base_continuity",
    "source_url",
    "review_status",
    "notes",
]

ALIAS_FIELDS = [
    "alias_record_id",
    "panel_id",
    "lineage_id",
    "utility_id_eia",
    "identity_role",
    "state",
    "source_system",
    "source_name",
    "normalized_name",
    "valid_from_year",
    "valid_to_year",
    "alias_type",
    "source_url",
    "review_status",
    "notes",
]

COVERAGE_FIELDS = [
    "panel_id",
    "lineage_id",
    "display_name",
    "state",
    "year",
    "current_utility_id_eia",
    "coverage_status",
    "reporting_basis",
    "matched_utility_ids_eia",
    "matched_utility_names_eia",
    "component_count",
    "all_ids_in_utility_file",
    "all_ids_in_sales_file",
    "source_url",
    "review_status",
    "notes",
]


def normalize_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def clean_text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def archive_path(year: int) -> Path:
    if year <= 2011:
        return RAW_REFORMATTED_DIR / f"861_{year}.zip"
    return RAW_OFFICIAL_DIR / f"f861{year}.zip"


def archive_url(year: int) -> str:
    if year <= 2011:
        return (
            "https://www.eia.gov/electricity/data/eia861/archive/zip/"
            f"861_{year}.zip"
        )
    if year == 2024:
        return "https://www.eia.gov/electricity/data/eia861/zip/f8612024.zip"
    return (
        "https://www.eia.gov/electricity/data/eia861/archive/zip/"
        f"f861{year}.zip"
    )


def find_member(archive: zipfile.ZipFile, token: str) -> str:
    matches = [
        name
        for name in archive.namelist()
        if token in Path(name).name.lower()
        and "_cs_" not in Path(name).name.lower()
        and Path(name).suffix.lower() in {".xls", ".xlsx"}
        and not Path(name).name.startswith("~")
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one {token} workbook; found {matches}")
    return matches[0]


def extract_workbook(
    archive: zipfile.ZipFile, member: str, label: str, workdir: Path
) -> Path:
    extracted_dir = workdir / f"extracted-{label}"
    extracted_dir.mkdir()
    extracted = extracted_dir / Path(member).name
    extracted.write_bytes(archive.read(member))
    if extracted.suffix.lower() == ".xlsx":
        return extracted

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError("LibreOffice is required to read legacy XLS files")
    converted_dir = workdir / f"converted-{label}"
    profile_dir = workdir / f"profile-{label}"
    converted_dir.mkdir()
    subprocess.run(
        [
            soffice,
            f"-env:UserInstallation={profile_dir.resolve().as_uri()}",
            "--headless",
            "--convert-to",
            "xlsx",
            "--outdir",
            str(converted_dir),
            str(extracted),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    converted = converted_dir / f"{extracted.stem}.xlsx"
    if not converted.exists():
        raise FileNotFoundError(f"Conversion did not create {converted}")
    return converted


def read_annual_records(
    year: int, workdir: Path
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    path = archive_path(year)
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Download it from {archive_url(year)}."
        )
    with zipfile.ZipFile(path) as archive:
        utility_member = find_member(archive, "utility_data")
        sales_member = find_member(archive, "sales_ult_cust")
        utility_workbook = extract_workbook(
            archive, utility_member, f"utility-{year}", workdir
        )
        sales_workbook = extract_workbook(
            archive, sales_member, f"sales-{year}", workdir
        )

    utility_raw = pd.read_excel(utility_workbook, sheet_name="States", header=1)
    utility_columns = {
        str(column).strip().lower(): column for column in utility_raw.columns
    }
    id_column = utility_columns["utility number"]
    name_column = utility_columns["utility name"]
    state_column = utility_columns["state"]
    utility_raw = utility_raw.loc[
        pd.to_numeric(utility_raw[id_column], errors="coerce").notna()
    ]
    utility_records = [
        {
            "year": year,
            "utility_id_eia": int(float(row[id_column])),
            "utility_name": clean_text(row[name_column]),
            "state": clean_text(row[state_column]),
        }
        for _, row in utility_raw.iterrows()
    ]

    sales_raw = pd.read_excel(
        sales_workbook, sheet_name="States", header=[0, 1, 2]
    )
    sales_raw = sales_raw.loc[
        pd.to_numeric(sales_raw.iloc[:, 1], errors="coerce").notna()
    ]
    sales_records = [
        {
            "year": year,
            "utility_id_eia": int(float(values[1])),
            "utility_name": clean_text(values[2]),
            "state": clean_text(values[6]),
            "service_type": clean_text(values[4]).lower(),
        }
        for values in sales_raw.itertuples(index=False, name=None)
    ]
    return utility_records, sales_records


def load_candidates() -> list[dict[str, str]]:
    with CANDIDATES_FILE.open(newline="", encoding="utf-8") as source:
        candidates = list(csv.DictReader(source))
    if len(candidates) != 42:
        raise ValueError(f"Expected 42 utilities; found {len(candidates)}")
    return candidates


def lineage_id(candidate: dict[str, str]) -> str:
    return f"LNG_{candidate['state']}_{candidate['utility_id_eia']}"


def component_ids(current_id: int, year: int) -> tuple[int, ...]:
    if current_id in PREDECESSORS and year <= PREDECESSOR_REPORTING_END[current_id]:
        return tuple(
            int(record["utility_id_eia"])
            for record in PREDECESSORS[current_id]
        )
    return (current_id,)


def lineage_components(current_id: int) -> tuple[dict[str, object], ...]:
    return (
        *PREDECESSORS.get(current_id, ()),
        *ABSORBED_COMPONENTS.get(current_id, ()),
    )


def consecutive_ranges(years: list[int]) -> list[tuple[int, int]]:
    if not years:
        return []
    ranges: list[tuple[int, int]] = []
    start = previous = years[0]
    for year in years[1:]:
        if year != previous + 1:
            ranges.append((start, previous))
            start = year
        previous = year
    ranges.append((start, previous))
    return ranges


def annual_index(
    records: list[dict[str, object]], include_service: bool = False
) -> dict[tuple[int, int, str], list[dict[str, object]]]:
    index: dict[tuple[int, int, str], list[dict[str, object]]] = defaultdict(list)
    for record in records:
        index[
            (
                int(record["year"]),
                int(record["utility_id_eia"]),
                str(record["state"]),
            )
        ].append(record)
    return index


def build_outputs() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    candidates = load_candidates()
    candidate_by_id = {int(row["utility_id_eia"]): row for row in candidates}
    predecessor_owner = {
        int(record["utility_id_eia"]): current_id
        for current_id in set(PREDECESSORS) | set(ABSORBED_COMPONENTS)
        for record in lineage_components(current_id)
    }
    tracked_ids = set(candidate_by_id) | set(predecessor_owner)

    utility_records: list[dict[str, object]] = []
    sales_records: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as temporary:
        workdir = Path(temporary)
        for year in range(YEAR_START, YEAR_END + 1):
            annual_utility, annual_sales = read_annual_records(year, workdir)
            utility_records.extend(
                record
                for record in annual_utility
                if int(record["utility_id_eia"]) in tracked_ids
            )
            sales_records.extend(
                record
                for record in annual_sales
                if int(record["utility_id_eia"]) in tracked_ids
            )

    utility_lookup: dict[tuple[int, int], list[dict[str, object]]] = defaultdict(list)
    for record in utility_records:
        utility_lookup[
            (int(record["year"]), int(record["utility_id_eia"]))
        ].append(record)
    sales_lookup = annual_index(sales_records, include_service=True)

    coverage_rows: list[dict[str, object]] = []
    for candidate in candidates:
        current_id = int(candidate["utility_id_eia"])
        state = candidate["state"]
        for year in range(YEAR_START, YEAR_END + 1):
            ids = component_ids(current_id, year)
            names: list[str] = []
            utility_presence: list[bool] = []
            sales_presence: list[bool] = []
            for utility_id in ids:
                utility_matches = utility_lookup.get((year, utility_id), [])
                sales_matches = sales_lookup.get((year, utility_id, state), [])
                utility_presence.append(bool(utility_matches))
                sales_presence.append(bool(sales_matches))
                reported_names = {
                    str(record["utility_name"])
                    for record in [*sales_matches, *utility_matches]
                    if str(record["utility_name"])
                }
                names.append(" / ".join(sorted(reported_names)))
            if not all(utility_presence) or not all(sales_presence):
                raise ValueError(
                    f"Incomplete identity connection for {current_id} in {year}: "
                    f"utility={utility_presence}, sales={sales_presence}"
                )
            predecessor_basis = ids != (current_id,)
            coverage_rows.append(
                {
                    "panel_id": candidate["panel_id"],
                    "lineage_id": lineage_id(candidate),
                    "display_name": candidate["display_name"],
                    "state": state,
                    "year": year,
                    "current_utility_id_eia": current_id,
                    "coverage_status": (
                        "matched_predecessor_combination"
                        if predecessor_basis
                        else "matched_current_id"
                    ),
                    "reporting_basis": (
                        "combined predecessor retail records"
                        if predecessor_basis
                        else "current EIA utility ID"
                    ),
                    "matched_utility_ids_eia": "|".join(map(str, ids)),
                    "matched_utility_names_eia": "|".join(names),
                    "component_count": len(ids),
                    "all_ids_in_utility_file": True,
                    "all_ids_in_sales_file": True,
                    "source_url": archive_url(year),
                    "review_status": "reviewed_phase_2",
                    "notes": (
                        "Annual retail reporting still uses the predecessor "
                        "utilities; combine their records for the current territory."
                        if predecessor_basis
                        else "The current EIA utility ID is present in both the annual "
                        "utility and retail-sales files."
                    ),
                }
            )

    # Build one reported-name row for each uninterrupted run in each source.
    alias_years: dict[tuple[str, int, str, str, str], list[int]] = defaultdict(list)
    for source_system, records in (
        ("EIA-861 Utility Data", utility_records),
        ("EIA-861 Sales to Ultimate Customers", sales_records),
    ):
        for record in records:
            utility_id = int(record["utility_id_eia"])
            current_id = predecessor_owner.get(utility_id, utility_id)
            candidate = candidate_by_id[current_id]
            if (
                source_system == "EIA-861 Sales to Ultimate Customers"
                and record["state"] != candidate["state"]
            ):
                continue
            name = str(record["utility_name"])
            if not name:
                continue
            key = (
                source_system,
                utility_id,
                candidate["state"],
                name,
                "predecessor_id" if utility_id in predecessor_owner else "current_id",
            )
            alias_years[key].append(int(record["year"]))

    alias_rows: list[dict[str, object]] = []
    alias_sequence = 0
    for key in sorted(alias_years, key=lambda value: (value[1], value[0], value[3])):
        source_system, utility_id, state, name, identity_role = key
        current_id = predecessor_owner.get(utility_id, utility_id)
        candidate = candidate_by_id[current_id]
        for valid_from, valid_to in consecutive_ranges(sorted(set(alias_years[key]))):
            alias_sequence += 1
            alias_rows.append(
                {
                    "alias_record_id": f"AL_{alias_sequence:04d}",
                    "panel_id": candidate["panel_id"],
                    "lineage_id": lineage_id(candidate),
                    "utility_id_eia": utility_id,
                    "identity_role": identity_role,
                    "state": state,
                    "source_system": source_system,
                    "source_name": name,
                    "normalized_name": normalize_name(name),
                    "valid_from_year": valid_from,
                    "valid_to_year": valid_to,
                    "alias_type": "annual_eia_reported_name",
                    "source_url": archive_url(valid_from),
                    "review_status": "reviewed_phase_2",
                    "notes": "Exact name printed in the official annual EIA file.",
                }
            )

    for year, utility_id, name in PUBLISHED_NAME_VARIANTS:
        alias_sequence += 1
        candidate = candidate_by_id[utility_id]
        alias_rows.append(
            {
                "alias_record_id": f"AL_{alias_sequence:04d}",
                "panel_id": candidate["panel_id"],
                "lineage_id": lineage_id(candidate),
                "utility_id_eia": utility_id,
                "identity_role": "current_id",
                "state": candidate["state"],
                "source_system": "EIA Electric Sales, Revenue, and Average Price",
                "source_name": name,
                "normalized_name": normalize_name(name),
                "valid_from_year": year,
                "valid_to_year": year,
                "alias_type": "published_table_name_variant",
                "source_url": (
                    "https://www.eia.gov/electricity/sales_revenue_price/archive/"
                    f"f861{year}.zip"
                ),
                "review_status": "reviewed_phase_2",
                "notes": (
                    "Word-order or department-name variant accepted for matching; "
                    "this is not a separate utility."
                ),
            }
        )

    aliases_by_id: dict[int, set[str]] = defaultdict(set)
    for row in alias_rows:
        aliases_by_id[int(row["utility_id_eia"])].add(str(row["source_name"]))

    lineage_rows: list[dict[str, object]] = []
    for candidate in candidates:
        current_id = int(candidate["utility_id_eia"])
        direct_years = sorted(
            {
                int(record["year"])
                for record in utility_records
                if int(record["utility_id_eia"]) == current_id
            }
        )
        if not direct_years:
            raise ValueError(f"No annual identity years found for {current_id}")
        predecessor_ids = [
            int(record["utility_id_eia"])
            for record in lineage_components(current_id)
        ]
        source_url = CURRENT_SOURCE_OVERRIDES.get(current_id, EIA_SOURCE_PAGE)
        if current_id == 54913:
            note = (
                "NSTAR Electric begins under the current EIA ID in 2007. Its "
                "retail predecessors are Boston Edison, Cambridge Electric, and "
                "Commonwealth Electric; Canal Electric was wholesale and is excluded."
            )
        elif current_id == 24590:
            note = (
                "Unitil Energy Systems exists in the 2002 identity file, but the "
                "2002 retail territory remains reported under Concord Electric and "
                "Exeter & Hampton. The current ID is the clean retail record from 2003."
            )
        elif current_id == 7601:
            note = (
                "Green Mountain Power keeps its current EIA ID, but its 2024 service "
                "territory includes Central Vermont Public Service, acquired in 2012. "
                "Phase 4 must decide whether to aggregate the older CVPS records for "
                "a fixed-territory comparison."
            )
        elif current_id == 1179:
            note = (
                "Bangor Hydro keeps the current EIA ID through its later Emera Maine "
                "and Versant names, but the 2024 territory also includes Maine Public "
                "Service, legally consolidated in 2014."
            )
        elif current_id == 19791:
            note = (
                "Vermont Electric Cooperative keeps its current EIA ID but materially "
                "expanded by acquiring Citizens' Vermont electric division in 2004. "
                "Citizens is visible in the 2001-2002 EIA retail files and absent in "
                "the 2003 reformatted file, so no 2003 component is forced."
            )
        else:
            note = (
                "The same EIA utility ID is present throughout the 2001-2024 review "
                "window; reported-name changes are listed in the name file."
            )
        lineage_rows.append(
            {
                "lineage_record_id": f"LR_{candidate['panel_id']}_{current_id}",
                "lineage_id": lineage_id(candidate),
                "panel_id": candidate["panel_id"],
                "utility_id_eia": current_id,
                "utility_name_eia": candidate["utility_name_eia"],
                "display_name": candidate["display_name"],
                "state": candidate["state"],
                "valid_from_year": min(direct_years),
                "valid_to_year": max(direct_years),
                "predecessor_utility_id_eia": "|".join(map(str, predecessor_ids)),
                "successor_utility_id_eia": "",
                "name_aliases": "|".join(sorted(aliases_by_id[current_id])),
                "service_territory_continuity": (
                    "combined_predecessor_territories"
                    if current_id in PREDECESSORS
                    else "expanded_by_absorbed_territory"
                    if current_id in ABSORBED_COMPONENTS
                    else "same_reported_utility_id"
                ),
                "customer_base_continuity": (
                    "transaction_source_confirms_predecessor_customers"
                    if current_id in PREDECESSORS
                    else "requires_phase_4_fixed_territory_decision"
                    if current_id in ABSORBED_COMPONENTS
                    else "same_reported_utility_id"
                ),
                "source_url": source_url,
                "review_status": (
                    "reviewed_phase_3"
                    if current_id in ABSORBED_COMPONENTS
                    else "reviewed_phase_2"
                ),
                "notes": note,
            }
        )
        for predecessor in lineage_components(current_id):
            predecessor_id = int(predecessor["utility_id_eia"])
            absorbed_component = predecessor in ABSORBED_COMPONENTS.get(
                current_id, ()
            )
            lineage_rows.append(
                {
                    "lineage_record_id": (
                        f"LR_{candidate['panel_id']}_{predecessor_id}"
                    ),
                    "lineage_id": lineage_id(candidate),
                    "panel_id": candidate["panel_id"],
                    "utility_id_eia": predecessor_id,
                    "utility_name_eia": predecessor["utility_name_eia"],
                    "display_name": candidate["display_name"],
                    "state": candidate["state"],
                    "valid_from_year": predecessor["valid_from_year"],
                    "valid_to_year": predecessor["valid_to_year"],
                    "predecessor_utility_id_eia": "",
                    "successor_utility_id_eia": current_id,
                    "name_aliases": "|".join(sorted(aliases_by_id[predecessor_id])),
                    "service_territory_continuity": (
                        "absorbed_into_current_service_territory"
                        if absorbed_component
                        else "combined_into_current_service_territory"
                    ),
                    "customer_base_continuity": (
                        "phase_4_aggregation_review_required"
                        if absorbed_component
                        else "transaction_source_confirms_predecessor_customers"
                    ),
                    "source_url": predecessor["source_url"],
                    "review_status": (
                        "reviewed_phase_3"
                        if absorbed_component
                        else "reviewed_phase_2"
                    ),
                    "notes": (
                        "Earlier utility whose customers were later absorbed into the "
                        "current service territory. It is recorded for Phase 4 review "
                        "and is not silently treated as the same legal utility."
                        if absorbed_component
                        else "Earlier retail utility included as a component of the "
                        "current service territory; annual observations are not treated "
                        "as a separate current utility."
                    ),
                }
            )

    return lineage_rows, alias_rows, coverage_rows


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    lineage_rows, alias_rows, coverage_rows = build_outputs()
    write_csv(LINEAGE_OUTPUT, LINEAGE_FIELDS, lineage_rows)
    write_csv(ALIASES_OUTPUT, ALIAS_FIELDS, alias_rows)
    write_csv(COVERAGE_OUTPUT, COVERAGE_FIELDS, coverage_rows)
    print(f"Wrote {len(lineage_rows)} utility-history rows to {LINEAGE_OUTPUT}")
    print(f"Wrote {len(alias_rows)} reported-name rows to {ALIASES_OUTPUT}")
    print(f"Wrote {len(coverage_rows)} annual coverage rows to {COVERAGE_OUTPUT}")


if __name__ == "__main__":
    main()
