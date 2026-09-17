# Reproducible environment

The project was fully rebuilt and tested on September 17, 2026 with:

- Python 3.12.10
- pandas 3.0.3
- NumPy 2.5.1
- DuckDB 1.5.4
- openpyxl 3.1.5
- Node.js 26.5.0
- LibreOfficeDev 26.8.0.0.alpha0, build
  `2c87e51eeaa2b413ff4ae097b2705eea1995d8e5`

The Python package versions are pinned in `requirements.txt`. Node.js uses only
built-in modules during the normal rebuild. LibreOffice's `soffice` command is
needed because the 2013 and 2014 EIA archives contain old `.xls` workbooks that
pandas does not read directly in this project.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 scripts/rebuild_project.py --check-only
```

Install Node.js and LibreOffice separately if the check reports that `node` or
`soffice` is missing. The rebuild stops early when a required package, command,
or frozen source file is absent.

## Normal rebuild

```bash
python3 scripts/rebuild_project.py
```

That command rebuilds the ROE source tables, price panels, reliability audit,
statistical models, ISO fuel-mix files, case-study files, and then runs the unit
tests. It uses `sys.executable`, so the same Python interpreter that launches
the workflow runs every Python stage.

To verify an extracted professor package, including every SHA-256 fingerprint,
the full rebuild, tests, and the generated data dictionary, run:

```bash
python3 scripts/verify_professor_handoff.py --rebuild
```

The optional formatted ROE workbook uses the `@oai/artifact-tool` Node package.
It is not required for the CSV data or website:

```bash
python3 scripts/rebuild_project.py --with-workbook
```
