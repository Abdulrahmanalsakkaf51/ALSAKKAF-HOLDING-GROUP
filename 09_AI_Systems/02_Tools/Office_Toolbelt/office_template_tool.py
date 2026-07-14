"""AOS Office Toolbelt - office template tool (PRJ-013). Standard library only.

Turns structured inputs into professional DOCX documents via document_tool:
  * management report
  * meeting minutes
  * business letter
"""

import datetime

import document_tool


def management_report(path, title, period, sections, metrics=None, prepared_by="AOS Office Partner"):
    """sections: list of {"heading", "text"}. metrics: list of [name, value]."""
    blocks = [
        {"type": "title", "text": title},
        {"type": "paragraph", "text": "Reporting period: %s" % period},
        {"type": "paragraph", "text": "Date prepared: %s" % datetime.date.today().isoformat()},
    ]
    if metrics:
        blocks.append({"type": "heading", "text": "Key Numbers", "level": 1})
        blocks.append({"type": "table", "headers": ["Metric", "Value"],
                       "rows": [[str(a), str(b)] for a, b in metrics]})
    for section in sections:
        blocks.append({"type": "heading", "text": section["heading"], "level": 1})
        blocks.append({"type": "paragraph", "text": section["text"]})
        for item in section.get("bullets", []):
            blocks.append({"type": "bullets", "items": [item]})
    blocks.append({"type": "note",
                   "text": "Prepared by %s (draft). Reviewed by: pending human review."
                           % prepared_by})
    return document_tool.create_document(path, blocks)


def meeting_minutes(path, meeting_title, date, attendees, notes, decisions, actions):
    """actions: list of {"item", "owner", "due"}."""
    blocks = [
        {"type": "title", "text": "Meeting Minutes — %s" % meeting_title},
        {"type": "paragraph", "text": "Date: %s" % date},
        {"type": "heading", "text": "Attendees", "level": 1},
        {"type": "bullets", "items": attendees},
        {"type": "heading", "text": "Discussion Notes", "level": 1},
        {"type": "bullets", "items": notes},
        {"type": "heading", "text": "Decisions", "level": 1},
        {"type": "bullets", "items": decisions or ["No decisions recorded."]},
        {"type": "heading", "text": "Action Items", "level": 1},
        {"type": "table", "headers": ["Action", "Owner", "Due"],
         "rows": [[a["item"], a["owner"], a["due"]] for a in actions]},
        {"type": "note", "text": "Drafted by AOS Office Partner from meeting notes. "
                                 "Accuracy to be confirmed by attendees."},
    ]
    return document_tool.create_document(path, blocks)


def business_letter(path, recipient_name, recipient_org, subject, body_paragraphs,
                    sender_name="Abdulrahman Alsakkaf", sender_title="Founder, ALSAKKAF Systems"):
    blocks = [
        {"type": "paragraph", "text": datetime.date.today().strftime("%d %B %Y")},
        {"type": "paragraph", "text": "%s\n%s" % (recipient_name, recipient_org)},
        {"type": "heading", "text": "Subject: %s" % subject, "level": 2},
        {"type": "paragraph", "text": "Dear %s," % recipient_name},
    ]
    for para in body_paragraphs:
        blocks.append({"type": "paragraph", "text": para})
    blocks.append({"type": "paragraph", "text": "Sincerely,"})
    blocks.append({"type": "paragraph", "text": "%s\n%s" % (sender_name, sender_title)})
    return document_tool.create_document(path, blocks)
