"""AOS Pod Tools - outreach composer (PRJ-014 pod). Standard library only.

Deterministic outreach drafting for the Client Acquisition role (PARTNER-019):
  * reads a VERIFIED lead (dict shaped like Lead_Tracker.csv)
  * chooses an approved offer from the catalog
  * generates a personalized first-touch draft and a follow-up draft

HARD RULES:
  * Never sends anything. Drafts only, marked NOT SENT.
  * Only approved offers with approved prices and approved payment links.
  * Refuses leads below the confidence threshold.
"""

APPROVED_OFFERS = {
    "AI Workflow Starter Pack": {
        "price": "$399 USD",
        "pitch": "a working lead-tracking system, one documented internal process, "
                 "and a simple owner dashboard",
        "keywords": ("workflow", "tracking", "process", "operations", "admin",
                     "documentation", "visibility", "manual"),
    },
    "AI Agent Starter Pack": {
        "price": "$450 USD",
        "pitch": "three custom AI agents (Manager, Research/Analyst, Operations) "
                 "built around your business, with prompts, routing, and a live setup session",
        "keywords": ("agent", "assistant", "ai", "research", "automation",
                     "delegate", "capacity"),
    },
}


class LeadNotReady(Exception):
    pass


def choose_offer(lead):
    """Pick the approved offer that best matches the observed problem."""
    stated = str(lead.get("Offer Match", "")).strip()
    if stated in APPROVED_OFFERS:
        return stated
    problem = str(lead.get("Problem Observed", "")).lower()
    best, best_hits = "AI Workflow Starter Pack", 0
    for name, offer in APPROVED_OFFERS.items():
        hits = sum(1 for k in offer["keywords"] if k in problem)
        if hits > best_hits:
            best, best_hits = name, hits
    return best


def compose_outreach(lead, confidence, sender="Abdulrahman"):
    """Build first-touch and follow-up drafts for a verified lead."""
    if confidence == "Low":
        raise LeadNotReady(
            "Lead %s is Low confidence — verify it before drafting outreach."
            % lead.get("Lead ID", "?"))
    offer_name = choose_offer(lead)
    offer = APPROVED_OFFERS[offer_name]
    contact = str(lead.get("Decision Maker", "")).strip() or "there"
    company = str(lead.get("Company Name", "")).strip() or "your company"
    problem = str(lead.get("Problem Observed", "")).strip()

    first = {
        "to": lead.get("Email", ""),
        "subject": "A practical fix for %s" % (problem[:60] or "your workflow"),
        "body": (
            "Hi %s,\n\n"
            "While researching %s I noticed: %s.\n\n"
            "That is exactly what our %s addresses — %s, for %s as one scoped "
            "engagement delivered in 5-7 business days.\n\n"
            "Would a short call this week be useful? If it is not a fit, a one-line "
            "reply saying so is completely fine.\n\n"
            "Best regards,\n%s\nALSAKKAF Systems — alsakkafsystems.com"
            % (contact, company, problem or "a workflow gap",
               offer_name, offer["pitch"], offer["price"], sender)),
        "status": "DRAFT — NOT SENT. A human reviews, edits, and sends this.",
        "offer": offer_name,
    }
    follow_up = {
        "to": lead.get("Email", ""),
        "subject": "RE: A practical fix — quick follow-up",
        "body": (
            "Hi %s,\n\n"
            "Following up on my note about %s. If the timing is wrong, no problem — "
            "happy to reconnect later or leave it here.\n\n"
            "If it would help, I can send a one-page summary of what the %s (%s) "
            "would look like for %s specifically.\n\n"
            "Best regards,\n%s"
            % (contact, problem or "your workflow", offer_name, offer["price"],
               company, sender)),
        "status": "DRAFT — NOT SENT. Send only after the first email got no reply for 3+ days.",
        "offer": offer_name,
    }
    return {"first_touch": first, "follow_up": follow_up}
