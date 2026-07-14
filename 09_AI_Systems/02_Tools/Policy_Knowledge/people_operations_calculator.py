"""AOS Policy and Law Knowledge System - people operations calculator (PRJ-014).

Deterministic calculators for common people-operations questions, using the
demo-pack rules (UAE private sector). Standard library only.

IMPORTANT: outputs are calculations from the demo knowledge pack, not legal
advice. Final decisions on leave, probation, and termination require human
HR/legal review.
"""

import datetime


def annual_leave_entitlement(service_months):
    """Days of annual leave per the demo pack rules."""
    if service_months >= 12:
        return {"days": 30, "basis": "30 calendar days per year after 1 year of service"}
    if service_months >= 6:
        return {"days": 2 * (service_months - 6),
                "basis": "2 days per month for service between 6 months and 1 year "
                         "(months beyond the first 6)"}
    return {"days": 0, "basis": "No statutory annual leave before 6 months of service "
                                "(company policy may grant more)"}


def probation_end(start_date, probation_months=6):
    """Latest lawful probation end date (max 6 months per demo pack)."""
    if probation_months > 6:
        raise ValueError("Probation may not exceed 6 months (PLK-UAE-005)")
    start = datetime.date.fromisoformat(str(start_date))
    month = start.month - 1 + probation_months
    year = start.year + month // 12
    month = month % 12 + 1
    day = min(start.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
                          else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return datetime.date(year, month, day)


def sick_leave_breakdown(days_taken):
    """Split sick days into full-pay / half-pay / unpaid tiers (15/30/45)."""
    if days_taken < 0:
        raise ValueError("days_taken must be >= 0")
    capped = min(days_taken, 90)
    full = min(capped, 15)
    half = min(max(capped - 15, 0), 30)
    unpaid = max(capped - 45, 0)
    return {"full_pay_days": full, "half_pay_days": half, "unpaid_days": unpaid,
            "beyond_entitlement_days": max(days_taken - 90, 0),
            "note": "90-day annual cap per PLK-UAE-003; exceeding it is a "
                    "LEGAL / HR REVIEW REQUIRED situation"}


def notice_period_check(contract_notice_days):
    """Validate a contractual notice period against the 30-90 day demo rule."""
    ok = 30 <= contract_notice_days <= 90
    return {"valid": ok,
            "note": ("Within the 30-90 day statutory range" if ok else
                     "OUTSIDE the 30-90 day range in PLK-UAE-006 — "
                     "LEGAL / HR REVIEW REQUIRED")}
