"""AOS Office Toolbelt - email draft tool (PRJ-013). Standard library only.

Drafts professional emails and extracts action items from message text.
HARD RULE: this tool NEVER sends anything. It writes draft files for a
human to review, edit, and send from their own mailbox.
"""

import datetime
import os
import re

SIGNATURE = "Best regards,\n{sender}\nALSAKKAF Systems — AOS AI Services"

TEMPLATES = {
    "reply": ("RE: {topic}",
              "Dear {recipient},\n\nThank you for your message regarding {topic}.\n\n"
              "{body}\n\nPlease let us know if you need anything further.\n\n"),
    "follow_up": ("Following up — {topic}",
                  "Dear {recipient},\n\nI wanted to follow up on {topic}.\n\n{body}\n\n"
                  "Would it help to schedule a short call this week?\n\n"),
    "meeting_confirmation": ("Meeting confirmation — {topic}",
                             "Dear {recipient},\n\nThis confirms our meeting about {topic}.\n\n"
                             "{body}\n\nWe look forward to speaking with you.\n\n"),
    "internal_update": ("Update — {topic}",
                        "Hello {recipient},\n\nA quick update on {topic}.\n\n{body}\n\n"),
}

ACTION_MARKERS = ("please", "need", "must", "required", "by ", "deadline",
                  "send", "confirm", "prepare", "schedule", "review")


def draft_email(kind, recipient, topic, body, sender="Abdulrahman"):
    """Return a draft dict. Nothing is sent."""
    if kind not in TEMPLATES:
        raise ValueError("Unknown template %r; options: %s" % (kind, sorted(TEMPLATES)))
    subject, template = TEMPLATES[kind]
    text = template.format(recipient=recipient, topic=topic, body=body)
    text += SIGNATURE.format(sender=sender)
    return {
        "subject": subject.format(topic=topic),
        "to": recipient,
        "body": text,
        "status": "DRAFT — requires human review and manual sending",
    }


def extract_action_items(message_text):
    """Deterministic action-item extraction: sentences containing action markers."""
    sentences = re.split(r"(?<=[.!?])\s+", message_text.replace("\n", " "))
    items = []
    for s in sentences:
        low = s.lower()
        if any(m in low for m in ACTION_MARKERS) and len(s.strip()) > 12:
            items.append(s.strip())
    return items


def save_draft(draft, out_dir, filename=None):
    """Write the draft to a Markdown file for human review."""
    os.makedirs(out_dir, exist_ok=True)
    filename = filename or ("email_draft_%s.md"
                            % datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    filename = os.path.basename(filename)
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Email Draft (NOT SENT)\n\n")
        f.write("| Field | Value |\n|-------|-------|\n")
        f.write("| To | %s |\n" % draft["to"])
        f.write("| Subject | %s |\n" % draft["subject"])
        f.write("| Status | %s |\n\n" % draft["status"])
        f.write("---\n\n")
        f.write(draft["body"] + "\n")
    return path
