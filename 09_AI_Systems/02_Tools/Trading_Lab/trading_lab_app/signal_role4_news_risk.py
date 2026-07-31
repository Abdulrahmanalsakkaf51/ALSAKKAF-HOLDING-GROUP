"""Role 4 — News/Event Risk Partner (TRL-R2-006 Section 2).

Checks governed news/economic-event evidence for the instrument within its
lookback window and flags elevated-risk windows. Consumes only the
already-governed ``news_context`` fixture the caller supplies (see
``signal_data.validate_news_context``) — never a live network call, never
raw text scraping. A HOLD/no-candidate evaluation always passes through:
there is nothing executable for this role to block.
"""

ROLE_NAME = "news_event_risk"
PASS = "PASS"
NEWS_EVENT_RISK_BLOCK = "NEWS_EVENT_RISK_BLOCK"

REASON_ELEVATED_RISK_WINDOW = "ELEVATED_RISK_WINDOW"


def evaluate(request, candidate_side):
    news = request["news_context"]
    evidence_ids = list(news["evidence_ids"])
    if candidate_side not in ("BUY", "SELL"):
        return {"status": PASS, "reasons": [], "evidence_ids": evidence_ids}
    if news["elevated_risk"]:
        reason = news["reason"] or REASON_ELEVATED_RISK_WINDOW
        return {
            "status": NEWS_EVENT_RISK_BLOCK,
            "reasons": [REASON_ELEVATED_RISK_WINDOW, reason] if reason != REASON_ELEVATED_RISK_WINDOW
            else [REASON_ELEVATED_RISK_WINDOW],
            "evidence_ids": evidence_ids,
        }
    return {"status": PASS, "reasons": [], "evidence_ids": evidence_ids}


__all__ = ("NEWS_EVENT_RISK_BLOCK", "PASS", "ROLE_NAME", "evaluate")
