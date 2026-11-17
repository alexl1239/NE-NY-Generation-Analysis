"""Build the Phase 3 ownership-change register and annual owner history.

This phase records reviewed transactions, distinguishes clean ownership-class
changes from consolidations and territory changes, and assigns a parent and
ownership class to every utility-year in the fixed 42-utility roster. It does
not build prices, estimate effects, or change the website.

Run: python3 scripts/build_ownership_history.py
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CANDIDATES_FILE = (
    PROJECT_ROOT / "data" / "processed" / "expanded_utility_candidates_2024.csv"
)
IDENTITY_COVERAGE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "utility_identity_coverage_2001_2024.csv"
)
EVENTS_OUTPUT = PROJECT_ROOT / "data" / "manual" / "ownership_events.csv"
SOURCES_OUTPUT = (
    PROJECT_ROOT / "data" / "manual" / "ownership_event_sources.csv"
)
ANNUAL_OUTPUT = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "utility_ownership_history_2001_2024.csv"
)

YEAR_START = 2001
YEAR_END = 2024
REVIEWED_DATE = "2026-11-14"

EVENT_FIELDS = [
    "event_id",
    "transaction_id",
    "lineage_id",
    "panel_id",
    "utility_id_eia",
    "utility_name",
    "state",
    "event_type",
    "event_scope",
    "analysis_role",
    "clean_ownership_change_candidate",
    "old_parent_name",
    "new_parent_name",
    "old_parent_country",
    "new_parent_country",
    "old_ownership_class",
    "new_ownership_class",
    "announcement_date",
    "regulatory_approval_date",
    "closing_date",
    "year_end_treatment_year",
    "first_full_treatment_year",
    "parent_changed",
    "ownership_class_changed",
    "utility_id_changed",
    "service_territory_changed",
    "source_ids",
    "primary_source_url",
    "secondary_source_url",
    "review_status",
    "reviewed_date",
    "notes",
]

SOURCE_FIELDS = [
    "source_id",
    "source_title",
    "publisher",
    "source_date",
    "source_type",
    "source_url",
    "local_source_path",
    "transactions_supported",
    "facts_supported",
    "review_status",
    "notes",
]

ANNUAL_FIELDS = [
    "panel_id",
    "lineage_id",
    "utility_id_eia",
    "display_name",
    "state",
    "year",
    "ultimate_parent_or_owner",
    "parent_country_or_level",
    "ownership_class",
    "owner_segment_start_year",
    "owner_segment_end_year",
    "event_in_year",
    "event_ids",
    "clean_class_change_in_year",
    "identity_reporting_basis",
    "matched_utility_ids_eia",
    "territory_comparability_status",
    "source_ids",
    "source_url",
    "review_status",
    "notes",
]


def source(
    source_id: str,
    title: str,
    publisher: str,
    source_date: str,
    source_type: str,
    source_url: str,
    transactions: str,
    facts: str,
    notes: str = "",
    local_path: str = "",
) -> dict[str, str]:
    return {
        "source_id": source_id,
        "source_title": title,
        "publisher": publisher,
        "source_date": source_date,
        "source_type": source_type,
        "source_url": source_url,
        "local_source_path": local_path,
        "transactions_supported": transactions,
        "facts_supported": facts,
        "review_status": "reviewed_phase_3",
        "notes": notes,
    }


SOURCES = [
    source(
        "PROJECT_2024_ROSTER",
        "Expanded 42-utility candidate roster",
        "Project review table",
        REVIEWED_DATE,
        "local_review_table",
        "",
        "stable-owner intervals",
        "2024 parent, ownership class, and utility-specific official source URL",
        "Used for utilities without an identified ownership event and for current-owner endpoints.",
        "data/processed/expanded_utility_candidates_2024.csv",
    ),
    source(
        "SEC_BANGOR_EMERA_2001",
        "Emera finalizes purchase of Bangor Hydro-Electric",
        "Bangor Hydro-Electric / Emera via SEC",
        "2001-10-10",
        "completion_filing",
        "https://www.sec.gov/Archives/edgar/data/9548/000000954801500012/bheem8ka.txt",
        "TXN_2001_EMERA_BANGOR",
        "closing date and Emera control",
    ),
    source(
        "SEC_NIMO_GRID_2002",
        "National Grid completes the acquisition of Niagara Mohawk",
        "National Grid via SEC",
        "2002-01-31",
        "completion_filing",
        "https://www.sec.gov/Archives/edgar/data/1004315/000100431502000005/form6-k.txt",
        "TXN_2002_GRID_NIMO",
        "announcement, final approval, closing date, and UK parent",
    ),
    source(
        "SEC_RGE_ENERGYEAST_2002",
        "Energy East 2002 Form 10-K",
        "Energy East via SEC",
        "2003-03-28",
        "annual_filing",
        "https://www.sec.gov/Archives/edgar/data/71675/000104686103000010/cmbktxt02.htm",
        "TXN_2002_ENERGYEAST_RGS",
        "June 28, 2002 acquisition of RGS Energy and RG&E relationship",
    ),
    source(
        "UNITIL_CONSOLIDATION_2002",
        "Unitil subsidiaries complete merger",
        "Unitil Corporation",
        "2002-12-02",
        "company_completion_release",
        "https://investors.unitil.com/news-releases/news-release-details/unitil-subsidiaries-complete-merger-and-implement-new-rates",
        "TXN_2002_UNITIL_CONSOLIDATION",
        "closing date, predecessor utilities, and successor name",
    ),
    source(
        "VEC_CITIZENS_HISTORY",
        "Vermont Electric Cooperative history",
        "Vermont Electric Cooperative",
        "",
        "company_history",
        "https://vermontelectric.coop/history",
        "TXN_2004_VEC_CITIZENS",
        "material territory expansion and acquired electric division",
    ),
    source(
        "SEC_CITIZENS_SALE_2004",
        "Citizens Communications 2006 Form 10-K",
        "Citizens Communications via SEC",
        "2007-03-01",
        "annual_filing",
        "https://www.sec.gov/Archives/edgar/data/20520/000002052007000009/form10k2006.txt",
        "TXN_2004_VEC_CITIZENS",
        "April 1, 2004 sale date for the Vermont electric division",
    ),
    source(
        "SEC_NSTAR_CONSOLIDATION_2007",
        "NSTAR Electric consolidation Form 8-K",
        "Boston Edison / NSTAR via SEC",
        "2007-01-05",
        "completion_filing",
        "https://www.sec.gov/Archives/edgar/data/13372/000001337207000002/beco8k010507.htm",
        "TXN_2007_NSTAR_CONSOLIDATION",
        "effective date, predecessor entities, and NSTAR Electric name",
    ),
    source(
        "SEC_GMP_GAZMETRO_2007",
        "Green Mountain Power merger completion Form 8-K",
        "Green Mountain Power via SEC",
        "2007-04-12",
        "completion_filing",
        "https://www.sec.gov/Archives/edgar/data/43704/000004370407000017/form_8-kmergercompletion.pdf",
        "TXN_2007_GAZMETRO_GMP",
        "closing date and Gaz Metro ownership",
    ),
    source(
        "SEC_IBERDROLA_ENERGYEAST_2008",
        "Energy East merger completion Form 8-K",
        "Energy East via SEC",
        "2008-09-16",
        "completion_filing",
        "https://www.sec.gov/Archives/edgar/data/1046861/000104686108000163/e8k091608.htm",
        "TXN_2008_IBERDROLA_ENERGYEAST",
        "closing date and Iberdrola control of Energy East",
    ),
    source(
        "SEC_EMERA_MPS_2010",
        "Emera interim financial statements",
        "Emera via SEC",
        "2011-05-10",
        "financial_filing",
        "https://www.sec.gov/Archives/edgar/data/1127248/000119312511126297/dex992.htm",
        "TXN_2010_EMERA_MAM",
        "December 21, 2010 acquisition of Maine & Maritimes, parent of MPS",
    ),
    source(
        "SEC_NU_NSTAR_2012",
        "NSTAR merger completion Form 8-K",
        "NSTAR via SEC",
        "2012-04-10",
        "completion_filing",
        "https://www.sec.gov/Archives/edgar/data/1035675/000119312512156335/d330724d8k.htm",
        "TXN_2012_NU_NSTAR",
        "closing date and Northeast Utilities control of NSTAR",
    ),
    source(
        "SEC_LIBERTY_GRANITE_2012",
        "Algonquin business acquisition report",
        "Algonquin Power & Utilities via SEC",
        "2012-08-08",
        "acquisition_report",
        "https://www.sec.gov/Archives/edgar/data/1174169/000119312512357263/d397496dex991.htm",
        "TXN_2012_ALGONQUIN_GRANITE",
        "July 3, 2012 acquisition of Granite State Electric from National Grid",
    ),
    source(
        "SEC_CVPS_GAZMETRO_2012",
        "Central Vermont Public Service merger completion Form 8-K",
        "Central Vermont Public Service via SEC",
        "2012-06-27",
        "completion_filing",
        "https://www.sec.gov/Archives/edgar/data/18808/000110465912046261/a12-15432_38k.htm",
        "TXN_2012_GAZMETRO_CVPS",
        "June 27 acquisition closing and Gaz Metro control",
    ),
    source(
        "GMP_CVPS_CONSOLIDATION_2012",
        "Green Mountain Power FERC Form 1",
        "Green Mountain Power",
        "2023-04-18",
        "regulatory_financial_filing",
        "https://gmpsnapshot.greenmountainpower.com/wp-content/uploads/2023/07/FERC-Form-1-2022-Q4.pdf",
        "TXN_2012_GMP_CVPS_CONSOLIDATION",
        "October 1, 2012 legal consolidation of CVPS into GMP",
    ),
    source(
        "SEC_CHG_FORTIS_2013",
        "Fortis completes acquisition of CH Energy Group",
        "CH Energy Group / Fortis via SEC",
        "2013-06-27",
        "completion_filing",
        "https://www.sec.gov/Archives/edgar/data/1061393/000119312513274933/d561415dex991.htm",
        "TXN_2013_FORTIS_CH_ENERGY",
        "approval and closing dates and Fortis control",
    ),
    source(
        "SEC_EMERA_MAINE_CONSOLIDATION_2014",
        "Emera Maine overview",
        "Emera via SEC",
        "2016-06-10",
        "financial_filing",
        "https://www.sec.gov/Archives/edgar/data/1127248/000119312516616784/d155277dex43.htm",
        "TXN_2014_EMERA_MAINE_CONSOLIDATION",
        "January 1, 2014 consolidation of Bangor Hydro and MPS",
    ),
    source(
        "SEC_UIL_IBERDROLA_2015",
        "Avangrid merger completion Form 8-K",
        "Avangrid via SEC",
        "2015-12-16",
        "completion_filing",
        "https://www.sec.gov/Archives/edgar/data/1634997/000119312515407879/d105528d8k.htm",
        "TXN_2015_IBERDROLA_UIL",
        "closing date and Iberdrola control of UIL",
    ),
    source(
        "ENMAX_EMERA_MAINE_2020",
        "ENMAX quarterly report",
        "ENMAX Corporation",
        "2020-06-30",
        "financial_report",
        "https://assets.enmax.com/api/public/content/7b03872560f14aec86eeae105caee82b?v=19f3e57d",
        "TXN_2020_ENMAX_EMERA_MAINE",
        "March 24, 2020 acquisition closing",
    ),
    source(
        "PPL_NARRAGANSETT_2022",
        "PPL completes acquisition of Rhode Island utility",
        "PPL Corporation",
        "2022-05-25",
        "company_completion_release",
        "https://investors.pplweb.com/2022-05-25-PPL-Corporation-completes-acquisition-of-Rhode-Islands-primary-electric-and-natural-gas-utility",
        "TXN_2022_PPL_NARRAGANSETT",
        "closing date, seller, buyer, and Rhode Island Energy rebrand",
    ),
]


def lineage_id(state: str, current_utility_id: int) -> str:
    return f"LNG_{state}_{current_utility_id}"


def event(
    event_id: str,
    transaction_id: str,
    panel_id: str,
    current_utility_id: int,
    event_utility_id: int,
    utility_name: str,
    state: str,
    event_type: str,
    event_scope: str,
    old_parent: str,
    new_parent: str,
    old_country: str,
    new_country: str,
    old_class: str,
    new_class: str,
    closing_date: str,
    source_ids: str,
    parent_changed: bool,
    utility_id_changed: bool,
    territory_changed: bool,
    notes: str,
    announcement_date: str = "",
    regulatory_approval_date: str = "",
) -> dict[str, object]:
    class_changed = old_class != new_class
    clean_candidate = (
        event_scope == "current_entity"
        and parent_changed
        and class_changed
        and not utility_id_changed
        and not territory_changed
    )
    if clean_candidate:
        analysis_role = "clean_class_change_candidate"
    elif event_scope == "absorbed_predecessor_component":
        analysis_role = "absorbed_predecessor_not_clean"
    elif utility_id_changed or territory_changed:
        analysis_role = "identity_or_boundary_change_not_clean"
    else:
        analysis_role = "same_class_parent_change"

    sources_by_id = {row["source_id"]: row for row in SOURCES}
    event_source_ids = source_ids.split("|")
    primary = sources_by_id[event_source_ids[0]]["source_url"]
    secondary = (
        sources_by_id[event_source_ids[1]]["source_url"]
        if len(event_source_ids) > 1
        else ""
    )
    closing_year = int(closing_date[:4])
    return {
        "event_id": event_id,
        "transaction_id": transaction_id,
        "lineage_id": lineage_id(state, current_utility_id),
        "panel_id": panel_id,
        "utility_id_eia": event_utility_id,
        "utility_name": utility_name,
        "state": state,
        "event_type": event_type,
        "event_scope": event_scope,
        "analysis_role": analysis_role,
        "clean_ownership_change_candidate": str(clean_candidate).lower(),
        "old_parent_name": old_parent,
        "new_parent_name": new_parent,
        "old_parent_country": old_country,
        "new_parent_country": new_country,
        "old_ownership_class": old_class,
        "new_ownership_class": new_class,
        "announcement_date": announcement_date,
        "regulatory_approval_date": regulatory_approval_date,
        "closing_date": closing_date,
        "year_end_treatment_year": closing_year,
        "first_full_treatment_year": closing_year + 1,
        "parent_changed": str(parent_changed).lower(),
        "ownership_class_changed": str(class_changed).lower(),
        "utility_id_changed": str(utility_id_changed).lower(),
        "service_territory_changed": str(territory_changed).lower(),
        "source_ids": source_ids,
        "primary_source_url": primary,
        "secondary_source_url": secondary,
        "review_status": "reviewed_phase_3",
        "reviewed_date": REVIEWED_DATE,
        "notes": notes,
    }


EVENTS = [
    event(
        "OWN_2001_BANGOR_01", "TXN_2001_EMERA_BANGOR", "MTC_ME_VERSANT",
        1179, 1179, "Bangor Hydro-Electric Company", "ME", "acquisition",
        "current_entity", "Bangor Hydro-Electric Company (independent)",
        "Emera Inc.", "United States", "Canada", "DOM", "MTC",
        "2001-10-10", "SEC_BANGOR_EMERA_2001", True, False, False,
        "The acquisition occurs inside the first panel year, so 2001 is a partial-treatment year and 2002 is the first full year.",
        "2000-06-29",
    ),
    event(
        "OWN_2002_NIMO_01", "TXN_2002_GRID_NIMO", "MTC_NY_NIMO",
        13573, 13573, "Niagara Mohawk Power Corporation", "NY", "acquisition",
        "current_entity", "Niagara Mohawk Holdings, Inc.", "National Grid plc",
        "United States", "United Kingdom", "DOM", "MTC", "2002-01-31",
        "SEC_NIMO_GRID_2002", True, False, False,
        "Only 2001 is available as a full pre-closing calendar year.",
        "2000-09-05", "2002-01-16",
    ),
    event(
        "OWN_2002_RGE_01", "TXN_2002_ENERGYEAST_RGS", "MTC_NY_RGE",
        16183, 16183, "Rochester Gas & Electric Corporation", "NY",
        "acquisition", "current_entity", "RGS Energy Group, Inc.",
        "Energy East Corporation", "United States", "United States", "DOM",
        "DOM", "2002-06-28", "SEC_RGE_ENERGYEAST_2002", True, False, False,
        "This is a real parent change but not an ownership-class change.",
    ),
    event(
        "CONS_2002_UNITIL_01", "TXN_2002_UNITIL_CONSOLIDATION", "DOM_NH_UNITIL",
        24590, 24590, "Unitil Energy Systems", "NH", "legal_consolidation",
        "legal_identity_consolidation", "Unitil Corporation", "Unitil Corporation",
        "United States", "United States", "DOM", "DOM", "2002-12-02",
        "UNITIL_CONSOLIDATION_2002", False, True, True,
        "Concord Electric and Exeter & Hampton combined under the current Unitil ID; this is not a clean ownership event.",
    ),
    event(
        "ASSET_2004_VEC_01", "TXN_2004_VEC_CITIZENS", "COOP_VT_VEC",
        19791, 3611, "Citizens Communications Company — Vermont Electric Division",
        "VT", "asset_acquisition", "absorbed_predecessor_component",
        "Citizens Communications Company", "Vermont Electric Cooperative",
        "United States", "Local/member-owned", "DOM", "COOP", "2004-04-01",
        "VEC_CITIZENS_HISTORY|SEC_CITIZENS_SALE_2004", True, True, True,
        "The acquired division more than doubled VEC membership. It changes the territory and customer base, so it is not a clean ownership comparison.",
    ),
    event(
        "CONS_2007_NSTAR_01", "TXN_2007_NSTAR_CONSOLIDATION", "DOM_MA_NSTAR",
        54913, 54913, "NSTAR Electric Company", "MA", "legal_consolidation",
        "legal_identity_consolidation", "NSTAR", "NSTAR", "United States",
        "United States", "DOM", "DOM", "2007-01-01",
        "SEC_NSTAR_CONSOLIDATION_2007", False, True, True,
        "Boston Edison, Cambridge Electric, and Commonwealth Electric retail territories were combined. Canal Electric was wholesale and is excluded from the retail history.",
    ),
    event(
        "OWN_2007_GMP_01", "TXN_2007_GAZMETRO_GMP", "MTC_VT_GMP",
        7601, 7601, "Green Mountain Power Corporation", "VT", "acquisition",
        "current_entity", "Green Mountain Power Corporation (independent)",
        "Gaz Metro Limited Partnership", "United States", "Canada", "DOM", "MTC",
        "2007-04-12", "SEC_GMP_GAZMETRO_2007", True, False, False,
        "The legal utility and EIA ID continue under a Canadian parent.",
        "2006-06-22", "2007-03-26",
    ),
    event(
        "OWN_2008_NYSEG_01", "TXN_2008_IBERDROLA_ENERGYEAST", "MTC_NY_NYSEG",
        13511, 13511, "New York State Electric & Gas Corporation", "NY",
        "acquisition", "current_entity", "Energy East Corporation", "Iberdrola S.A.",
        "United States", "Spain", "DOM", "MTC", "2008-09-16",
        "SEC_IBERDROLA_ENERGYEAST_2008", True, False, False,
        "One Energy East transaction changes the parent of NYSEG, CMP, and RG&E.",
        "2007-06-25",
    ),
    event(
        "OWN_2008_CMP_01", "TXN_2008_IBERDROLA_ENERGYEAST", "MTC_ME_CMP",
        3266, 3266, "Central Maine Power Company", "ME", "acquisition",
        "current_entity", "Energy East Corporation", "Iberdrola S.A.",
        "United States", "Spain", "DOM", "MTC", "2008-09-16",
        "SEC_IBERDROLA_ENERGYEAST_2008", True, False, False,
        "One Energy East transaction changes the parent of NYSEG, CMP, and RG&E.",
        "2007-06-25",
    ),
    event(
        "OWN_2008_RGE_01", "TXN_2008_IBERDROLA_ENERGYEAST", "MTC_NY_RGE",
        16183, 16183, "Rochester Gas & Electric Corporation", "NY", "acquisition",
        "current_entity", "Energy East Corporation", "Iberdrola S.A.",
        "United States", "Spain", "DOM", "MTC", "2008-09-16",
        "SEC_IBERDROLA_ENERGYEAST_2008", True, False, False,
        "One Energy East transaction changes the parent of NYSEG, CMP, and RG&E.",
        "2007-06-25",
    ),
    event(
        "OWN_2010_MPS_01", "TXN_2010_EMERA_MAM", "MTC_ME_VERSANT",
        1179, 11522, "Maine Public Service Company", "ME", "acquisition",
        "absorbed_predecessor_component", "Maine & Maritimes Corporation",
        "Emera Inc.", "United States", "Canada", "DOM", "MTC", "2010-12-21",
        "SEC_EMERA_MPS_2010", True, False, False,
        "MPS was acquired before its 2014 legal consolidation with Bangor Hydro. It is an absorbed predecessor, not a clean current-entity event.",
        "2010-03-12",
    ),
    event(
        "OWN_2012_NSTAR_01", "TXN_2012_NU_NSTAR", "DOM_MA_NSTAR",
        54913, 54913, "NSTAR Electric Company", "MA", "acquisition",
        "current_entity", "NSTAR", "Northeast Utilities", "United States",
        "United States", "DOM", "DOM", "2012-04-10", "SEC_NU_NSTAR_2012",
        True, False, False,
        "NSTAR changed parent within the domestic investor-owned class. Northeast Utilities later adopted the Eversource name.",
        "2010-10-18",
    ),
    event(
        "OWN_2012_LIBERTY_01", "TXN_2012_ALGONQUIN_GRANITE", "MTC_NH_LIBERTY",
        26510, 26510, "Granite State Electric Company", "NH", "acquisition",
        "current_entity", "National Grid plc", "Algonquin Power & Utilities Corp.",
        "United Kingdom", "Canada", "MTC", "MTC", "2012-07-03",
        "SEC_LIBERTY_GRANITE_2012", True, False, False,
        "The foreign parent changes from National Grid to Algonquin, but the ownership class remains MTC.",
        "2010-12-08",
    ),
    event(
        "OWN_2012_CVPS_01", "TXN_2012_GAZMETRO_CVPS", "MTC_VT_GMP",
        7601, 3292, "Central Vermont Public Service Corporation", "VT",
        "acquisition", "absorbed_predecessor_component",
        "Central Vermont Public Service Corporation (independent)",
        "Gaz Metro Limited Partnership", "United States", "Canada", "DOM", "MTC",
        "2012-06-27", "SEC_CVPS_GAZMETRO_2012", True, False, False,
        "CVPS changed ownership before being legally consolidated into GMP. It is tracked as an absorbed predecessor.",
        "2011-07-12", "2012-06-15",
    ),
    event(
        "CONS_2012_GMP_CVPS_01", "TXN_2012_GMP_CVPS_CONSOLIDATION", "MTC_VT_GMP",
        7601, 7601, "Green Mountain Power Corporation", "VT",
        "legal_consolidation", "legal_identity_consolidation",
        "Gaz Metro Limited Partnership", "Gaz Metro Limited Partnership", "Canada",
        "Canada", "MTC", "MTC", "2012-10-01",
        "GMP_CVPS_CONSOLIDATION_2012", False, True, True,
        "CVPS merged into GMP, materially expanding the current GMP territory. This is a boundary and identity change, not a clean ownership event.",
    ),
    event(
        "OWN_2013_CENTHUD_01", "TXN_2013_FORTIS_CH_ENERGY", "MTC_NY_CENTHUD",
        3249, 3249, "Central Hudson Gas & Electric Corporation", "NY",
        "acquisition", "current_entity", "CH Energy Group, Inc.", "Fortis Inc.",
        "United States", "Canada", "DOM", "MTC", "2013-06-27",
        "SEC_CHG_FORTIS_2013", True, False, False,
        "The year-end rule codes 2013 as MTC; 2014 is the first full outcome year under Fortis.",
        regulatory_approval_date="2013-06-26",
    ),
    event(
        "CONS_2014_EMERA_MAINE_01", "TXN_2014_EMERA_MAINE_CONSOLIDATION",
        "MTC_ME_VERSANT", 1179, 1179, "Emera Maine", "ME",
        "legal_consolidation", "legal_identity_consolidation", "Emera Inc.",
        "Emera Inc.", "Canada", "Canada", "MTC", "MTC", "2014-01-01",
        "SEC_EMERA_MAINE_CONSOLIDATION_2014", False, True, True,
        "Bangor Hydro and Maine Public Service became Emera Maine, expanding the territory attached to current EIA ID 1179.",
    ),
    event(
        "OWN_2015_UI_01", "TXN_2015_IBERDROLA_UIL", "MTC_CT_UI",
        19497, 19497, "United Illuminating Company", "CT", "acquisition",
        "current_entity", "UIL Holdings Corporation",
        "Iberdrola S.A. through Avangrid", "United States", "Spain", "DOM", "MTC",
        "2015-12-16", "SEC_UIL_IBERDROLA_2015", True, False, False,
        "The first full outcome year under Iberdrola is 2016.",
    ),
    event(
        "OWN_2020_VERSANT_01", "TXN_2020_ENMAX_EMERA_MAINE", "MTC_ME_VERSANT",
        1179, 1179, "Versant Power", "ME", "acquisition", "current_entity",
        "Emera Inc.", "ENMAX Corporation", "Canada", "Canada", "MTC", "MTC",
        "2020-03-24", "ENMAX_EMERA_MAINE_2020", True, False, False,
        "Emera Maine was renamed Versant Power in May 2020. This is a parent change without an ownership-class change.",
    ),
    event(
        "OWN_2022_RIE_01", "TXN_2022_PPL_NARRAGANSETT", "DOM_RI_RIE",
        13214, 13214, "The Narragansett Electric Company", "RI", "acquisition",
        "current_entity", "National Grid plc", "PPL Corporation", "United Kingdom",
        "United States", "MTC", "DOM", "2022-05-25", "PPL_NARRAGANSETT_2022",
        True, False, False,
        "Operations were rebranded Rhode Island Energy at closing; 2023 is the first full outcome year under PPL.",
    ),
]


def segment(
    start: int,
    end: int,
    parent: str,
    country: str,
    ownership_class: str,
    source_ids: str,
    source_url: str,
    notes: str = "",
) -> dict[str, object]:
    return {
        "start": start,
        "end": end,
        "parent": parent,
        "country": country,
        "ownership_class": ownership_class,
        "source_ids": source_ids,
        "source_url": source_url,
        "notes": notes,
    }


SOURCE_URL = {row["source_id"]: row["source_url"] for row in SOURCES}

PARENT_SEGMENTS = {
    "MTC_NY_NIMO": [
        segment(2001, 2001, "Niagara Mohawk Holdings, Inc.", "United States", "DOM", "SEC_NIMO_GRID_2002", SOURCE_URL["SEC_NIMO_GRID_2002"]),
        segment(2002, 2024, "National Grid plc", "United Kingdom", "MTC", "SEC_NIMO_GRID_2002", SOURCE_URL["SEC_NIMO_GRID_2002"]),
    ],
    "MTC_NY_NYSEG": [
        segment(2001, 2007, "Energy East Corporation", "United States", "DOM", "SEC_IBERDROLA_ENERGYEAST_2008", SOURCE_URL["SEC_IBERDROLA_ENERGYEAST_2008"]),
        segment(2008, 2024, "Iberdrola S.A. through Avangrid", "Spain", "MTC", "SEC_IBERDROLA_ENERGYEAST_2008", SOURCE_URL["SEC_IBERDROLA_ENERGYEAST_2008"]),
    ],
    "MTC_ME_CMP": [
        segment(2001, 2007, "Energy East Corporation", "United States", "DOM", "SEC_IBERDROLA_ENERGYEAST_2008", SOURCE_URL["SEC_IBERDROLA_ENERGYEAST_2008"]),
        segment(2008, 2024, "Iberdrola S.A. through Avangrid", "Spain", "MTC", "SEC_IBERDROLA_ENERGYEAST_2008", SOURCE_URL["SEC_IBERDROLA_ENERGYEAST_2008"]),
    ],
    "MTC_NY_RGE": [
        segment(2001, 2001, "RGS Energy Group, Inc.", "United States", "DOM", "SEC_RGE_ENERGYEAST_2002", SOURCE_URL["SEC_RGE_ENERGYEAST_2002"]),
        segment(2002, 2007, "Energy East Corporation", "United States", "DOM", "SEC_RGE_ENERGYEAST_2002", SOURCE_URL["SEC_RGE_ENERGYEAST_2002"]),
        segment(2008, 2024, "Iberdrola S.A. through Avangrid", "Spain", "MTC", "SEC_IBERDROLA_ENERGYEAST_2008", SOURCE_URL["SEC_IBERDROLA_ENERGYEAST_2008"]),
    ],
    "DOM_MA_NSTAR": [
        segment(2001, 2011, "NSTAR", "United States", "DOM", "SEC_NSTAR_CONSOLIDATION_2007", SOURCE_URL["SEC_NSTAR_CONSOLIDATION_2007"]),
        segment(2012, 2024, "Northeast Utilities / Eversource Energy", "United States", "DOM", "SEC_NU_NSTAR_2012", SOURCE_URL["SEC_NU_NSTAR_2012"], "Northeast Utilities adopted the Eversource name in 2015; this name change is not a new ownership event."),
    ],
    "DOM_CT_CLP": [
        segment(2001, 2024, "Northeast Utilities / Eversource Energy", "United States", "DOM", "PROJECT_2024_ROSTER", "", "The parent company adopted the Eversource name in 2015 without a control change."),
    ],
    "DOM_NH_PSNH": [
        segment(2001, 2024, "Northeast Utilities / Eversource Energy", "United States", "DOM", "PROJECT_2024_ROSTER", "", "The parent company adopted the Eversource name in 2015 without a control change."),
    ],
    "DOM_RI_RIE": [
        segment(2001, 2021, "National Grid plc", "United Kingdom", "MTC", "PPL_NARRAGANSETT_2022", SOURCE_URL["PPL_NARRAGANSETT_2022"]),
        segment(2022, 2024, "PPL Corporation", "United States", "DOM", "PPL_NARRAGANSETT_2022", SOURCE_URL["PPL_NARRAGANSETT_2022"]),
    ],
    "MTC_CT_UI": [
        segment(2001, 2014, "UIL Holdings Corporation", "United States", "DOM", "SEC_UIL_IBERDROLA_2015", SOURCE_URL["SEC_UIL_IBERDROLA_2015"]),
        segment(2015, 2024, "Iberdrola S.A. through Avangrid", "Spain", "MTC", "SEC_UIL_IBERDROLA_2015", SOURCE_URL["SEC_UIL_IBERDROLA_2015"]),
    ],
    "MTC_NY_CENTHUD": [
        segment(2001, 2012, "CH Energy Group, Inc.", "United States", "DOM", "SEC_CHG_FORTIS_2013", SOURCE_URL["SEC_CHG_FORTIS_2013"]),
        segment(2013, 2024, "Fortis Inc.", "Canada", "MTC", "SEC_CHG_FORTIS_2013", SOURCE_URL["SEC_CHG_FORTIS_2013"]),
    ],
    "MTC_VT_GMP": [
        segment(2001, 2006, "Green Mountain Power Corporation (independent)", "United States", "DOM", "SEC_GMP_GAZMETRO_2007", SOURCE_URL["SEC_GMP_GAZMETRO_2007"]),
        segment(2007, 2024, "Gaz Metro / Energir", "Canada", "MTC", "SEC_GMP_GAZMETRO_2007", SOURCE_URL["SEC_GMP_GAZMETRO_2007"], "Gaz Metro later adopted the Energir name; the rename is not a control change."),
    ],
    "MTC_ME_VERSANT": [
        segment(2001, 2019, "Emera Inc.", "Canada", "MTC", "SEC_BANGOR_EMERA_2001", SOURCE_URL["SEC_BANGOR_EMERA_2001"]),
        segment(2020, 2024, "ENMAX Corporation", "Canada", "MTC", "ENMAX_EMERA_MAINE_2020", SOURCE_URL["ENMAX_EMERA_MAINE_2020"]),
    ],
    "MTC_NH_LIBERTY": [
        segment(2001, 2011, "National Grid plc", "United Kingdom", "MTC", "SEC_LIBERTY_GRANITE_2012", SOURCE_URL["SEC_LIBERTY_GRANITE_2012"]),
        segment(2012, 2024, "Algonquin Power & Utilities Corp.", "Canada", "MTC", "SEC_LIBERTY_GRANITE_2012", SOURCE_URL["SEC_LIBERTY_GRANITE_2012"]),
    ],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source_file:
        return list(csv.DictReader(source_file))


def write_csv(
    path: Path, fields: list[str], rows: list[dict[str, object]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def territory_status(panel_id: str, year: int) -> tuple[str, str]:
    if panel_id == "DOM_MA_NSTAR" and year <= 2006:
        return (
            "combined_predecessor_entities",
            "Retail data use Boston Edison, Cambridge Electric, and Commonwealth Electric before the NSTAR Electric consolidation.",
        )
    if panel_id == "DOM_NH_UNITIL" and year <= 2002:
        return (
            "combined_predecessor_entities",
            "Retail data use Concord Electric and Exeter & Hampton before the Unitil Energy Systems consolidation.",
        )
    if panel_id == "MTC_VT_GMP" and year <= 2012:
        return (
            "pre_acquisition_territory",
            "The current GMP territory later absorbed CVPS; Phase 4 must decide whether to aggregate CVPS for a fixed-territory series.",
        )
    if panel_id == "MTC_ME_VERSANT" and year <= 2013:
        return (
            "pre_acquisition_territory",
            "The current Versant territory later absorbed Maine Public Service; Phase 4 must decide whether to aggregate MPS for a fixed-territory series.",
        )
    if panel_id == "COOP_VT_VEC" and year <= 2003:
        return (
            "pre_major_acquisition_territory",
            "VEC had not yet acquired Citizens' Vermont division. Citizens is present in the 2001-2002 EIA retail files but absent from the 2003 reformatted file.",
        )
    return "current_reported_entity", ""


def build_annual_rows() -> list[dict[str, object]]:
    candidates = read_csv(CANDIDATES_FILE)
    coverage = read_csv(IDENTITY_COVERAGE_FILE)
    if len(candidates) != 42:
        raise ValueError(f"Expected 42 roster utilities; found {len(candidates)}")

    coverage_by_key = {
        (row["panel_id"], int(row["year"])): row for row in coverage
    }
    events_by_key: dict[tuple[str, int], list[dict[str, object]]] = defaultdict(list)
    for row in EVENTS:
        events_by_key[(str(row["panel_id"]), int(row["year_end_treatment_year"]))].append(row)

    annual_rows: list[dict[str, object]] = []
    for candidate in candidates:
        panel_id = candidate["panel_id"]
        segments = PARENT_SEGMENTS.get(panel_id)
        if segments is None:
            segments = [
                segment(
                    YEAR_START,
                    YEAR_END,
                    candidate["ultimate_parent_or_owner_2024"],
                    candidate["parent_country_or_level"],
                    candidate["ownership_2024"],
                    "PROJECT_2024_ROSTER",
                    candidate["ownership_source_url"],
                    "No material ownership change was identified in the Phase 3 event review.",
                )
            ]

        for year in range(YEAR_START, YEAR_END + 1):
            matches = [
                owner_segment
                for owner_segment in segments
                if int(owner_segment["start"]) <= year <= int(owner_segment["end"])
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"Expected one parent segment for {panel_id} in {year}; found {matches}"
                )
            owner_segment = matches[0]
            annual_events = events_by_key.get((panel_id, year), [])
            event_ids = [str(row["event_id"]) for row in annual_events]
            event_source_ids = {
                source_id
                for row in annual_events
                for source_id in str(row["source_ids"]).split("|")
            }
            segment_source_ids = set(str(owner_segment["source_ids"]).split("|"))
            source_ids = "|".join(sorted(segment_source_ids | event_source_ids))
            coverage_row = coverage_by_key[(panel_id, year)]
            status, territory_note = territory_status(panel_id, year)
            notes = " ".join(
                item
                for item in [str(owner_segment["notes"]), territory_note]
                if item
            )
            annual_rows.append(
                {
                    "panel_id": panel_id,
                    "lineage_id": lineage_id(
                        candidate["state"], int(candidate["utility_id_eia"])
                    ),
                    "utility_id_eia": int(candidate["utility_id_eia"]),
                    "display_name": candidate["display_name"],
                    "state": candidate["state"],
                    "year": year,
                    "ultimate_parent_or_owner": owner_segment["parent"],
                    "parent_country_or_level": owner_segment["country"],
                    "ownership_class": owner_segment["ownership_class"],
                    "owner_segment_start_year": owner_segment["start"],
                    "owner_segment_end_year": owner_segment["end"],
                    "event_in_year": str(bool(annual_events)).lower(),
                    "event_ids": "|".join(event_ids),
                    "clean_class_change_in_year": str(
                        any(
                            row["clean_ownership_change_candidate"] == "true"
                            for row in annual_events
                        )
                    ).lower(),
                    "identity_reporting_basis": coverage_row["reporting_basis"],
                    "matched_utility_ids_eia": coverage_row[
                        "matched_utility_ids_eia"
                    ],
                    "territory_comparability_status": status,
                    "source_ids": source_ids,
                    "source_url": owner_segment["source_url"],
                    "review_status": "reviewed_phase_3",
                    "notes": notes,
                }
            )
    return annual_rows


def validate(annual_rows: list[dict[str, object]]) -> None:
    source_ids = [str(row["source_id"]) for row in SOURCES]
    if len(source_ids) != len(set(source_ids)):
        raise ValueError("Duplicate source IDs")
    event_ids = [str(row["event_id"]) for row in EVENTS]
    if len(event_ids) != len(set(event_ids)):
        raise ValueError("Duplicate event IDs")
    if len(EVENTS) != 20:
        raise ValueError(f"Expected 20 reviewed event rows; found {len(EVENTS)}")
    if len(annual_rows) != 42 * 24:
        raise ValueError(f"Expected 1,008 annual rows; found {len(annual_rows)}")
    annual_keys = {(row["panel_id"], row["year"]) for row in annual_rows}
    if len(annual_keys) != len(annual_rows):
        raise ValueError("Duplicate annual ownership keys")
    known_sources = set(source_ids)
    for row in [*EVENTS, *annual_rows]:
        unknown = set(str(row["source_ids"]).split("|")) - known_sources
        if unknown:
            raise ValueError(f"Unknown source IDs {unknown} in {row}")
    for row in EVENTS:
        closing_year = int(str(row["closing_date"])[:4])
        if int(row["year_end_treatment_year"]) != closing_year:
            raise ValueError(f"Treatment-year mismatch for {row['event_id']}")
        if int(row["first_full_treatment_year"]) != closing_year + 1:
            raise ValueError(f"Full-year mismatch for {row['event_id']}")
    clean_rows = [
        row
        for row in EVENTS
        if row["clean_ownership_change_candidate"] == "true"
    ]
    if len(clean_rows) != 9:
        raise ValueError(f"Expected 9 clean event rows; found {len(clean_rows)}")
    if len({row["transaction_id"] for row in clean_rows}) != 7:
        raise ValueError("Expected 7 distinct clean ownership transactions")


def main() -> None:
    annual_rows = build_annual_rows()
    validate(annual_rows)
    write_csv(EVENTS_OUTPUT, EVENT_FIELDS, EVENTS)
    write_csv(SOURCES_OUTPUT, SOURCE_FIELDS, SOURCES)
    write_csv(ANNUAL_OUTPUT, ANNUAL_FIELDS, annual_rows)
    print(f"Wrote {len(EVENTS)} reviewed ownership-event rows to {EVENTS_OUTPUT}")
    print(f"Wrote {len(SOURCES)} ownership-source rows to {SOURCES_OUTPUT}")
    print(f"Wrote {len(annual_rows)} utility-year owner rows to {ANNUAL_OUTPUT}")


if __name__ == "__main__":
    main()
