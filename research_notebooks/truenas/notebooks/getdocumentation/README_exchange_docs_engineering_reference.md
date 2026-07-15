# Exchange Docs Engineering Reference

This script builds a stronger offline bundle for MEXC spot, MEXC futures, and NONKYC.

What it improves over the earlier bundle:

- extracts per-endpoint detail sections instead of only a normalized catalog
- extracts request / response parameter tables where the official docs provide them
- writes richer WebSocket sections with examples and notes
- normalizes canonical REST and WS bases
- fixes misleading MEXC spot auth presentation by separating headers from signed query/body params
- resolves NONKYC relative links to absolute URLs
- audits official NONKYC client source for suspicious definitions and shadowed functions
- writes `source_issues.md`
- writes machine-readable `_raw/catalog.json`

Outputs written to `./documents` include:

- `exchange_docs.md`
- `mexc_spot_v3.md`
- `mexc_futures.md`
- `nonkyc.md`
- `validation_report.md`
- `observed_schemas.md`
- `undocumented_fields.md`
- `discrepancies.md`
- `source_issues.md`
- `quality_report.md`
- `_raw/catalog.json`

Run:

```bash
pip install -r requirements-exchange-docs-engineering-reference.txt
python -u scrape_exchange_docs_engineering_reference.py
```

Notebook cell:

```python
import sys
!{sys.executable} -m pip install -r /notebooks/getdocumentation/requirements-exchange-docs-engineering-reference.txt
!{sys.executable} -u /notebooks/getdocumentation/scrape_exchange_docs_engineering_reference.py 2>&1 | tee /notebooks/getdocumentation/run.log
```

Notes:

- The script still avoids live order placement by default.
- It performs authenticated checks only when credentials are provided through environment variables supported by the existing validator.
- MEXC futures private REST may warn if the API key lacks read permission even when private WS login works.
