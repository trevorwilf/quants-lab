"""Re-export shim: quality.py now lives in bowaka_common.quality.reports.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.quality.reports import (  # noqa: F401
    DailyAuditResult,
    audit_daily_bars,
    IntradayAuditResult,
    audit_intraday_bars,
    QuoteAuditResult,
    audit_quotes,
    quote_age_at,
)

__all__ = ['DailyAuditResult', 'audit_daily_bars', 'IntradayAuditResult', 'audit_intraday_bars', 'QuoteAuditResult', 'audit_quotes', 'quote_age_at']
