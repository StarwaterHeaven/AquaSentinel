# Backtest — score as of 2024-01-01 vs what the field later found

Every record used is dated before the cutoff (register, inspections,
job cards, committee SMS, water tests, rainfall). Committee finances are
excluded — they did not exist yet. Ground truth comes from observations
after the cutoff only.

### vs Aug-2025 verification survey (124 points observed, 35 non-functional)

| signal | points | share found non-functional | share of non-functional caught |
|---|---|---|---|
| Flagged Not working / Critical | 36 | 47% | 49% |
| Silent (no fresh evidence) | 65 | 31% | 57% |
| — base rate (all points) | 124 | 28% | — |

### vs 2024 inspection round (624 points observed, 130 non-functional)

| signal | points | share found non-functional | share of non-functional caught |
|---|---|---|---|
| Flagged Not working / Critical | 201 | 47% | 72% |
| Silent (no fresh evidence) | 271 | 25% | 52% |
| — base rate (all points) | 624 | 21% | — |

## Reading

- Precision answers the officer's question: *if I spend a crew day on the
  flagged list, how often is the pump really down?*
- Recall answers the funder's question: *of the pumps that failed, how many
  were already on our list?*
- Silent points are the fairness net: no fresh evidence, so they go on the
  inspection list instead of being mistaken for healthy.
- Ground truth is observational: a pump repaired between cutoff and survey
  counts as a false positive even though the flag was right at the time.
  That makes these numbers a lower bound on usefulness.
