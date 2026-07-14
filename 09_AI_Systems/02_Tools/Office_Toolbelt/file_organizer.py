"""AOS Office Toolbelt - file organizer (PRJ-013). Standard library only.

Organizes business folders safely:
  * classify files by extension into category folders
  * apply the AOS naming convention (YYYY-MM-DD_Category_Description.ext)
  * detect duplicate files by content hash
  * build a Markdown folder index

Safety: NEVER deletes anything. Duplicates are reported, not removed.
Moves happen only inside the target folder being organized.
"""

import datetime
import hashlib
import os
import re
import shutil

CATEGORIES = {
    "Documents": {".doc", ".docx", ".pdf", ".txt", ".md", ".rtf", ".odt"},
    "Spreadsheets": {".xls", ".xlsx", ".csv", ".ods"},
    "Presentations": {".ppt", ".pptx", ".odp"},
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".svg", ".bmp", ".webp"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Data": {".json", ".xml", ".sqlite3", ".db"},
}


def categorize(filename):
    ext = os.path.splitext(filename)[1].lower()
    for category, exts in CATEGORIES.items():
        if ext in exts:
            return category
    return "Other"


def safe_name(description):
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", description).strip("_")
    return cleaned or "File"


def convention_name(original_name, category, date=None):
    date = date or datetime.date.today().isoformat()
    stem, ext = os.path.splitext(original_name)
    if re.match(r"^\d{4}-\d{2}-\d{2}_", stem):
        return original_name  # already conventional
    return "%s_%s_%s%s" % (date, category, safe_name(stem), ext.lower())


def find_duplicates(folder):
    """Return {hash: [paths]} for files with identical content (recursive)."""
    hashes = {}
    for root, _dirs, files in os.walk(folder):
        for name in files:
            path = os.path.join(root, name)
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            hashes.setdefault(h.hexdigest(), []).append(path)
    return {k: v for k, v in hashes.items() if len(v) > 1}


def organize_folder(folder, rename=True, date=None):
    """Classify loose files in `folder` into category subfolders.
    Returns a report dict. Never deletes; never leaves `folder`."""
    folder = os.path.abspath(folder)
    moved = []
    for name in sorted(os.listdir(folder)):
        src = os.path.join(folder, name)
        if not os.path.isfile(src):
            continue
        category = categorize(name)
        target_dir = os.path.join(folder, category)
        os.makedirs(target_dir, exist_ok=True)
        new_name = convention_name(name, category, date=date) if rename else name
        dst = os.path.join(target_dir, new_name)
        counter = 1
        while os.path.exists(dst):
            stem, ext = os.path.splitext(new_name)
            dst = os.path.join(target_dir, "%s_%d%s" % (stem, counter, ext))
            counter += 1
        shutil.move(src, dst)
        moved.append({"from": name, "to": os.path.relpath(dst, folder)})
    duplicates = find_duplicates(folder)
    return {"moved": moved, "duplicates": duplicates}


def build_index(folder, out_name="INDEX.md", title=None):
    """Write a Markdown index of the folder tree. Returns the index path."""
    folder = os.path.abspath(folder)
    title = title or os.path.basename(folder)
    lines = ["# Folder Index — %s" % title, "",
             "Generated: %s" % datetime.date.today().isoformat(), ""]
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        rel = os.path.relpath(root, folder)
        if rel != ".":
            lines.append("## %s" % rel.replace(os.sep, " / "))
            lines.append("")
        for name in sorted(files):
            if name == out_name:
                continue
            size = os.path.getsize(os.path.join(root, name))
            lines.append("- %s (%d bytes)" % (name, size))
        if files:
            lines.append("")
    path = os.path.join(folder, out_name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path
