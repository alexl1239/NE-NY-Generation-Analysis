# Optional tools

This directory contains special-purpose workflows that consume the core project
data but are not part of `scripts/rebuild_project.py`.

| Tool | Purpose | Generated output |
| --- | --- | --- |
| [`professor_handoff/`](professor_handoff/) | Build and verify a portable, checksummed review package | `outputs/professor-handoff/` |
| [`paper_figures/`](paper_figures/) | Export paper-ready price time-series JPEGs | `outputs/paper-figures/` |

Keeping these workflows here prevents one-off documents, images, and packaging
logic from becoming dependencies of the main analysis. Generated artifacts stay
under the ignored `outputs/` directory and should not be copied into `site/` or
`data/processed/` unless they become an intentional project deliverable.
