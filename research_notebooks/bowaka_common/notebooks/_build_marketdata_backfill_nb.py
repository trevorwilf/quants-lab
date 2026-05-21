"""Build research_notebooks/bowaka_common/notebooks/marketdata_backfill.ipynb.

Run: python research_notebooks/bowaka_common/notebooks/_build_marketdata_backfill_nb.py
"""
from __future__ import annotations

from pathlib import Path

import nbformat

HERE = Path(__file__).resolve().parent

_BOOTSTRAP = """\
# bowaka_common notebook bootstrap — DO NOT EDIT BY HAND.
# Locates the repo root, pins CWD there (so config/ paths resolve), and puts
# bowaka_common on sys.path — works under jupyter, papermill, and the scheduler.
import os
import sys
from pathlib import Path

_repo = None
for _c in [Path.cwd(), *Path.cwd().parents]:
    if (_c / "Makefile").is_file() and (_c / "research_notebooks").is_dir():
        _repo = _c
        break
if _repo is None:
    raise RuntimeError("could not locate the quants-lab repo root")
os.chdir(_repo)
_src = _repo / "research_notebooks" / "bowaka_common" / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

import bowaka_common  # noqa: F401
print(f"bowaka_common {bowaka_common.__version__} (cwd={_repo})")
"""

_PARAMS = """\
# Papermill parameters — override the config inline, or leave None to use the YAML.
CONFIG_PATH = "config/marketdata_backfill.yml"
FEED = None         # "iex" or "sip" to override config.feed
START_DATE = None   # "YYYY-MM-DD" to override config.start_date
END_DATE = None     # "YYYY-MM-DD" or "auto" to override config.end_date
"""

_INTRO = """\
# Market-data lake — manual backfill

Edit `config/marketdata_backfill.yml` (feed, date range, universe) — or set the
parameter cell above — then **Run All**. The backfill is incremental: only data
missing from the lake is fetched, so re-running is cheap and safe. Switching
`feed` between `iex` and `sip` writes a separate partition.

Requires `ALPACA_API_KEY_ID` / `ALPACA_API_SECRET_KEY` in the environment.
"""

_RUN = """\
import json
from bowaka_common.marketdata.runner import load_backfill_config, run_configured_backfill

config = load_backfill_config(CONFIG_PATH)
if FEED:
    config["feed"] = FEED
if START_DATE:
    config["start_date"] = START_DATE
if END_DATE:
    config["end_date"] = END_DATE

print(f"backfill: feed={config['feed']} "
      f"range={config['start_date']}..{config.get('end_date', 'auto')}")
result = run_configured_backfill(config)
print(json.dumps(result, indent=2, default=str))
"""


def main() -> None:
    nb = nbformat.v4.new_notebook()
    nb["cells"] = [
        nbformat.v4.new_code_cell(source=_BOOTSTRAP),
        nbformat.v4.new_code_cell(source=_PARAMS),
        nbformat.v4.new_markdown_cell(source=_INTRO),
        nbformat.v4.new_code_cell(source=_RUN),
    ]
    nb["metadata"] = {
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
        "papermill": {"parameters": {"CONFIG_PATH": "config/marketdata_backfill.yml"}},
    }
    out = HERE / "marketdata_backfill.ipynb"
    with out.open("w", encoding="utf-8") as fh:
        nbformat.write(nb, fh)
    print(f"Built {out}")


if __name__ == "__main__":
    main()
