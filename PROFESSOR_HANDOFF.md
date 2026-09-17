# Professor handoff guide

This package contains the raw source files and code needed to rebuild the website's data and test the main claims. Start with this file, then use `README.md` for the research summary.

## What is included

| Folder or file | Purpose |
| --- | --- |
| `data/raw/` | Frozen EIA and PUDL source files used by the rebuild |
| `data/manual/` | Small source-check tables reviewed by hand |
| `data/processed/` | Analysis-ready tables and exact model results |
| `scripts/` | Code that validates sources, builds the data, runs the models, creates the dictionary, and packages the handoff |
| `tests/` | Automated checks for data coverage, calculations, model outputs, and website claims |
| `site/` | The three-page website and browser-ready copies of the data |
| `docs/data-dictionary.csv` | Field-by-field profile of every delivered CSV |
| `docs/` | Methods, limitations, environment versions, and the human-readable dictionary guide |
| `SHA256SUMS.txt` | A SHA-256 fingerprint for every other file in this package |

Only files used by the current project are included. Older base-rate PDFs, duplicate extracts, planning notes, caches, and Git history are not part of this handoff.

## Fast verification

Use Python 3.12 with the package versions in `requirements.txt`. Node.js and LibreOffice are also required. From the extracted package folder, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 scripts/verify_professor_handoff.py --rebuild
```

The verifier performs these checks in a temporary or extracted copy:

1. Recalculate every file fingerprint and compare it with `SHA256SUMS.txt`.
2. Confirm the exact Python packages, Node.js, LibreOffice, and raw inputs are present.
3. Rebuild every current processed-data and website-data file without internet access.
4. Run the complete unit-test suite.
5. Confirm the data dictionary still matches all CSV files.
6. Recalculate every fingerprint after the rebuild. A match shows that the build reproduced the packaged files byte for byte.

Local `.venv`, Python cache, test cache, and `.DS_Store` files are ignored by the
fingerprint comparison because they are created by the reviewer's computer. No
delivered research, code, documentation, or website file is ignored.

If the environment is already prepared, the shorter commands are:

```bash
python3 scripts/rebuild_project.py --check-only
python3 scripts/rebuild_project.py
python3 scripts/build_data_dictionary.py --check
```

## How to check that the evidence was not invented

- Open `SHA256SUMS.txt`. A fingerprint changes if even one byte in a file changes. The verifier confirms that the received files match the packaged files.
- Read `data/raw/README.md` to see the exact frozen source inputs and retrieval dates.
- Compare `data/processed/reliability_source_validation_2013_2024.csv` with the official EIA archives in `data/raw/eia861/official/`. The project records 2,841 field comparisons and zero mismatches.
- Follow any ROE `source_ids` from `data/processed/roe_annual_pilot_2013_2024.csv` to `data/processed/roe_source_register.csv`. Each identifier resolves to a named public document and source location.
- Run the rebuild and tests. If code, data, and displayed claims disagree, the tests stop with an error.
- Read the methods in `docs/`. They explain selections, missing values, exclusions, model formulas, and known limits. Blank source values remain blank rather than being filled with zero.

For an ownership spot check, open
`data/processed/expanded_utility_candidates_2024.csv` and verify three parts of
the same row: EIA entity type, ultimate parent or public owner, and analytical
category. The rule is MTC for a foreign or multinational investor-owned parent,
DOM for a U.S.-based investor-owned parent, SOE for direct state-level public
ownership, and COOP for local municipal, member, cooperative, or community
ownership. `legal_ownership_description` keeps municipal utilities distinct from
member-owned cooperatives. No selected utility is SOE. Annual classifications use
the owner in place on December 31.

These checks establish file integrity, reproducibility, and agreement with the cited source records. They do not turn an observational result into a causal result.

## Main limits

- The price and reliability panels are selected samples, not random or complete samples of every utility in New York and New England.
- The models estimate associations. They do not prove that ownership causes a price or reliability difference.
- State and year controls do not capture every regulatory, customer, infrastructure, contract, or weather difference.
- Reliability reporting methods vary. Two documented NSTAR source conflicts are retained in the audit but withheld from the affected analysis fields.
- Regional generation mix does not identify an individual utility's contracts or delivered power mix.
- The authorized-ROE section is a six-utility matched-state descriptive check, not a regional ROE model.

## Package integrity files

`SHA256SUMS.txt` is inside the ZIP and covers every other delivered file. A second `.zip.sha256` file is created next to the ZIP and fingerprints the ZIP itself. The clean-room verification report is also created next to the ZIP so the preparation check is separate from the research files.
