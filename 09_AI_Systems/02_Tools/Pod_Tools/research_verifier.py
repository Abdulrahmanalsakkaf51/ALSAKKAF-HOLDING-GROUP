"""AOS Pod Tools - research verifier (PRJ-014 pod). Standard library only.

Deterministic lead verification for the Research / Market Intelligence role
(PARTNER-004). Works on rows shaped like Lead_Tracker.csv.

Checks:
  * required fields present
  * official website source (not only a social profile)
  * missing evidence (problem observed / offer match)
  * duplicate detection (by email, website domain, or normalized company name)
  * confidence classification: High / Medium / Low

No network calls: this verifies record quality, not live websites.
Live URL checks require Founder approval and are out of scope for v1.
"""

import csv
import re

REQUIRED_FIELDS = ["Company Name", "Industry", "Country", "Website",
                   "Decision Maker", "Problem Observed", "Offer Match"]

SOCIAL_DOMAINS = ("linkedin.com", "facebook.com", "instagram.com", "x.com",
                  "twitter.com", "tiktok.com", "youtube.com")

PLACEHOLDER_MARKERS = ("example only", "sample row", "not real", "not a real",
                       "template row", "illustrates column usage")


def _domain(url):
    m = re.match(r"https?://(?:www\.)?([^/]+)", str(url or "").strip().lower())
    return m.group(1) if m else ""


def is_placeholder(lead):
    blob = " ".join(str(v) for v in lead.values()).lower()
    return any(m in blob for m in PLACEHOLDER_MARKERS)


def verify_lead(lead):
    """Return a verification report for one lead row (dict)."""
    missing = [f for f in REQUIRED_FIELDS if not str(lead.get(f, "")).strip()]
    domain = _domain(lead.get("Website"))
    has_official_site = bool(domain) and not any(s in domain for s in SOCIAL_DOMAINS)
    evidence_missing = []
    if not str(lead.get("Problem Observed", "")).strip():
        evidence_missing.append("Problem Observed")
    if not str(lead.get("Offer Match", "")).strip():
        evidence_missing.append("Offer Match")

    if not missing and has_official_site:
        confidence = "High"
    elif not missing:
        confidence = "Medium"
    else:
        confidence = "Low"

    notes = []
    if missing:
        notes.append("Missing required fields: %s" % ", ".join(missing))
    if not has_official_site:
        notes.append("No official website source (social-only or blank)")
    if evidence_missing:
        notes.append("Missing evidence: %s" % ", ".join(evidence_missing))
    if is_placeholder(lead):
        confidence = "Low"
        notes.append("Row looks like a placeholder/example — not a real lead")

    return {"lead_id": lead.get("Lead ID", ""), "confidence": confidence,
            "missing_fields": missing, "official_website": has_official_site,
            "evidence_missing": evidence_missing, "notes": notes}


def find_duplicate_leads(leads):
    """Group leads that share an email, website domain, or normalized company name."""
    groups = {}
    for lead in leads:
        keys = set()
        email = str(lead.get("Email", "")).strip().lower()
        if email and "@" in email:
            keys.add("email:" + email)
        domain = _domain(lead.get("Website"))
        if domain:
            keys.add("domain:" + domain)
        company = re.sub(r"[^a-z0-9]", "", str(lead.get("Company Name", "")).lower())
        if company:
            keys.add("company:" + company)
        for key in keys:
            groups.setdefault(key, []).append(lead.get("Lead ID", "?"))
    return {k: v for k, v in groups.items() if len(set(v)) > 1}


def verify_tracker(csv_path):
    """Verify every lead in a Lead_Tracker.csv file."""
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        leads = list(csv.DictReader(f))
    reports = [verify_lead(lead) for lead in leads]
    duplicates = find_duplicate_leads(leads)
    summary = {"total": len(leads)}
    for level in ("High", "Medium", "Low"):
        summary[level.lower()] = sum(1 for r in reports if r["confidence"] == level)
    summary["duplicate_groups"] = len(duplicates)
    return {"summary": summary, "reports": reports, "duplicates": duplicates}
