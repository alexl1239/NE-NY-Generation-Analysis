# Paper figure exporter

This optional tool exports three paper-ready JPEGs showing annual median real
prices by ownership group for residential, commercial, and industrial customers.
It uses the processed 42-utility panel and the same CPI-U series as the core price
models.

Install the core dependencies and the optional image dependency, then run from
the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -r tools/paper_figures/requirements.txt
python3 tools/paper_figures/build_price_timeseries.py
```

The images are written to `outputs/paper-figures/`, which is ignored by Git. Use
`--output-dir` to choose another location. This exporter is not part of the
offline project rebuild and does not modify the public site.
