# AGENTS.md — kalshi-ev-finder

Finds positive expected value NFL betting opportunities on Kalshi.
Flat Python scripts at repo root.

## Run

- `python main.py` — scans for +EV opportunities.
- `python main.py paper [min_ev] [bet_size]` — generates paper trades
  (defaults: min EV 2.0%, bet size $20).

## Test & lint

- No test suite, no linter config (as of Oct 2026). Python 3.11, flat layout —
  match the existing style: plain scripts, no `src/` package.

## Conventions

- Deps aren't pinned anywhere machine-readable (no requirements.txt at root
  as of Oct 2026; previously: requests, pandas, python-dotenv, openpyxl,
  cryptography, schedule, kalshi-py). If you add a dependency, pin it.
- `.xlsx` workbooks are committed to the repo — they're working data, not
  build artifacts. Don't delete them.
- Ask before assuming. Change nothing until Eli approves.
