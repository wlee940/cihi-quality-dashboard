# CIHI quality dashboard, Cambridge Memorial Hospital

A monitoring dashboard for the Chief of Staff office. It tracks the quality indicators
CIHI publishes for Cambridge Memorial Hospital, separated into CIHI's own framework
categories, with trend history and a red / slate / green status per indicator, alongside
the hospital's own Quality Improvement Plan targets.

Published as a Claude Dashboard artifact:
<https://claude.ai/artifact/CZdfDsXHPXiswYWqhPigcH>

## What it shows

**15 graded indicators** in three categories — 3 above the Canadian average, 10 no
different from it, 2 below.

| Category | Indicators |
| --- | --- |
| Safe | in-hospital sepsis, obstetric trauma with and without instrument |
| Appropriate and effective | HSMR, deaths after major surgery, 30-day AMI mortality, readmission for all / medical / surgical / obstetric / pediatric patients, low-risk C-section |
| Access to high-quality services | ED wait to physician, total ED time for admitted patients, hip fracture surgery within 48 hours |

Plus the **six QIP 2026/27 commitments**, scored against the hospital's own targets
rather than against other hospitals.

### Status is CIHI's own comparison, not a local threshold

The colour comes from CIHI's published `Performance comparison` field, which is
significance-tested against the Canadian average given the hospital's case volume:

| Status | CIHI comparison | Colour |
| --- | --- | --- |
| Above average | `Above average performance`, `Lower than average` | green |
| Same as average | `Same as average performance` | slate |
| Below average | `Below average performance`, `Increasing more than average` | red |

Slate is the normal result and is not a problem to solve — at this hospital's volume the
confidence interval is wide, so only a large gap reaches significance. The middle band
is deliberately a neutral grey rather than an amber warning for that reason.

### What is deliberately left out

- **CIHI's contextual measures** (occupancy, length of stay, alternate level of care
  days, volumes, frailty). CIHI assigns them no performance comparison, so there is
  nothing to grade.
- **30-day stroke in-hospital mortality.** CIHI suppressed it for 2025&ndash;2026
  because there were too few cases to report.
- **Cost of a standard hospital stay**, and with it the whole *Efficiently delivered*
  category, which held nothing else.

All three are still present in `data/indicators.csv` and are filtered out by one rule
in the page (`isShown`), so any of them is a one-line restore.

## Layout

```
dashboard/index.html              the dashboard page
data/indicators.csv               latest published result per indicator (25 rows)
data/trend.csv                    every published year per indicator (197 rows)
data/targets.csv                  the six QIP 2026/27 commitments
data/source/cihi-cmh-rows.csv     CIHI's raw rows for this hospital
data/source/cihi-benchmark-rows.csv  Canada and Ontario rows for the same indicators
data/source/indicator-meta.csv    HSP framework dimension and interpretation per indicator
scripts/build_cihi.py             builds indicators.csv and trend.csv
scripts/build_targets.py          builds targets.csv
scripts/pdftxt.py                 extracts text from the QIP PDFs
scripts/parse_qip.py              splits that text into indicator blocks
```

## The page does not run standalone

`dashboard/index.html` is the source of a Claude Dashboard artifact, not a self-contained
web page. It expects the host runtime to provide:

- `dash.data(id)`, `dash.draw(name, fn)` and `dash.calc(id, {...})`
- `d3` as a global (v7)
- the design tokens it styles against (`--color-fg`, `--color-panel`, `--cds-pad-*`, and
  the rest)

Opening it directly in a browser will render the fixed text and nothing else. The three
datasets live in the artifact's own store, pointing at uploaded copies of the CSVs in
`data/`.

It also follows the artifact type's one-writer rule: every piece of fixed text lives in
the HTML, and scripts only fill elements marked `data-draw="name"`.

## Rebuilding the data

CIHI publishes the whole Indicator Library as one bulk CSV, about 543 MB and 1.34 M rows,
linked from [Download indicator data][dl]. That file is not in this repository; the two
extracts under `data/source/` are taken from it. To rebuild from scratch:

```bash
# 1. download the bulk file, then cut it down to this hospital and its benchmarks
#    (data/source/ already holds the result of this step)
# 2. rebuild the derived datasets
python3 scripts/build_cihi.py
python3 scripts/build_targets.py data/targets.csv
```

`build_cihi.py` takes only `Main metric == Yes` and `Breakdowns == Not applicable` rows.
It prefers `Reporting level == Corporation`, falling back to `Facility` for the few
measures CIHI publishes only against the physical site. It also overrides CIHI's
`Unit of measure` column for several contextual measures, where that column is wrong.

## Caveats carried on the page

- **CIHI re-baselined HSMR in 2026**, so the whole series is restated and older published
  HSMR figures will not match.
- Risk-adjusted rates are revised whenever CIHI updates its models.
- Reporting years differ by indicator. 14 of the 15 are 2025&ndash;2026; the low-risk
  caesarean rate is still on 2024&ndash;2025 because CIHI has not refreshed it.
- The QIP and CIHI figures for the ED wait to physician cover different periods — 7.40
  hours for Dec 2024 to Nov 2025 in the QIP, 7.60 hours for 2025&ndash;2026 in CIHI's
  series. Same NACRS measure, not a discrepancy.
- The data is a fixed copy of an annual publication, not a live query.

## Sources

- [CIHI, Download indicator data][dl]
- [CIHI, Acute care dashboard](https://www.cihi.ca/en/dashboards/acute-care)
- [CIHI, Indicator Library](https://www.cihi.ca/en/access-data-and-reports/indicator-library)
- Cambridge Memorial Hospital, Quality Improvement Plan workplans 2026/27 and 2025/26
  (Org ID 661)

CIHI data accessed 29 October 2026; CIHI refresh date 2026-08-26. Peer group
*Community &mdash; Medium*.

[dl]: https://www.cihi.ca/en/access-data-and-reports/indicator-library/download-indicator-data
