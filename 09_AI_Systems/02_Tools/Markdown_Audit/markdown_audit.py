import re
from pathlib import Path
from collections import defaultdict

TOOL_FILE = Path(__file__).resolve()
REPO_ROOT = TOOL_FILE.parents[3]

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules"
}

VERY_SHORT_FILE_LINE_LIMIT = 10


def should_skip_path(path):
    """Skip technical folders that should not be scanned."""
    return any(part in EXCLUDED_DIRS for part in path.parts)


def read_file(path):
    """Read a text file safely."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def add_issue(issues, file_path, issue_type, line_number, message, severity):
    """Add one issue to the issue list."""
    issues.append({
        "file_path": str(file_path),
        "issue_type": issue_type,
        "line_number": line_number,
        "message": message,
        "severity": severity
    })


def check_unclosed_code_blocks(relative_path, lines, issues):
    """
    Detect Markdown code blocks that start with ``` but do not close.
    """
    fence_open = False
    opening_line = None

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith("```"):
            fence_open = not fence_open

            if fence_open:
                opening_line = index
            else:
                opening_line = None

    if fence_open:
        add_issue(
            issues,
            relative_path,
            "Unclosed Code Block",
            opening_line,
            "A Markdown code block was opened but not closed.",
            "Error"
        )


def split_table_row(line):
    """Split a Markdown table row into cells."""
    stripped = line.strip()

    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None

    cells = stripped.strip("|").split("|")
    return [cell.strip() for cell in cells]


def is_table_separator(line):
    """Detect Markdown table separator rows like |---|---|."""
    cells = split_table_row(line)

    if not cells:
        return False

    for cell in cells:
        clean = cell.replace(":", "").replace("-", "").strip()
        if clean:
            return False

    return True


def check_broken_tables(relative_path, lines, issues):
    """
    Detect possible broken Markdown tables.

    This check looks for a table separator row and then compares column counts
    in the table rows around it.
    """
    index = 0

    while index < len(lines):
        line = lines[index]

        if not is_table_separator(line):
            index += 1
            continue

        separator_line_number = index + 1

        if index == 0:
            add_issue(
                issues,
                relative_path,
                "Possible Broken Table",
                separator_line_number,
                "Table separator appears without a header row above it.",
                "Warning"
            )
            index += 1
            continue

        header_cells = split_table_row(lines[index - 1])

        if not header_cells:
            add_issue(
                issues,
                relative_path,
                "Possible Broken Table",
                separator_line_number,
                "Table separator appears but the header row above it does not look like a table row.",
                "Warning"
            )
            index += 1
            continue

        expected_columns = len(header_cells)

        # Check header, separator, and rows below until table ends.
        table_start = index - 1
        table_end = index + 1

        while table_end < len(lines):
            row_cells = split_table_row(lines[table_end])
            if not row_cells:
                break

            if len(row_cells) != expected_columns:
                add_issue(
                    issues,
                    relative_path,
                    "Possible Broken Table",
                    table_end + 1,
                    f"Table row has {len(row_cells)} columns but header has {expected_columns}.",
                    "Warning"
                )

            table_end += 1

        index = table_end


def check_missing_document_information(relative_path, text, issues):
    """Detect files missing Document Information."""
    filename = Path(relative_path).name.lower()

    # README files may not need Document Information.
    if filename == "readme.md":
        return

    if "document information" not in text.lower():
        add_issue(
            issues,
            relative_path,
            "Missing Document Information",
            1,
            "This file does not appear to include a Document Information section.",
            "Warning"
        )


def check_status_field(relative_path, text, issues):
    """Detect important documents missing a Status field."""
    filename = Path(relative_path).name.lower()

    if filename == "readme.md":
        return

    lower_text = text.lower()

    if "document information" in lower_text and "| status |" not in lower_text:
        add_issue(
            issues,
            relative_path,
            "Missing Status Field",
            1,
            "Document Information section may be missing a Status row.",
            "Warning"
        )


def check_empty_or_short_file(relative_path, lines, issues):
    """Detect empty or very short Markdown files."""
    non_empty_lines = [line for line in lines if line.strip()]

    if not non_empty_lines:
        add_issue(
            issues,
            relative_path,
            "Empty File",
            1,
            "This Markdown file appears to be empty.",
            "Error"
        )
        return

    if len(non_empty_lines) <= VERY_SHORT_FILE_LINE_LIMIT:
        add_issue(
            issues,
            relative_path,
            "Very Short File",
            1,
            f"This Markdown file has only {len(non_empty_lines)} non-empty lines and may be incomplete.",
            "Info"
        )


def is_project_record(relative_path):
    """Detect project record files."""
    path_text = str(relative_path).replace("\\", "/")
    filename = Path(relative_path).name

    return (
        "01_Holding_Company/04_Operations/01_Project_Records/" in path_text
        and filename.startswith("PRJ-")
        and filename.endswith(".md")
        and "Lessons_Learned" not in filename
    )


def check_project_record_completeness(relative_path, text, issues):
    """Detect missing sections in project records."""
    if not is_project_record(relative_path):
        return

    lower_text = text.lower()

    if "project tasks" not in lower_text:
        add_issue(
            issues,
            relative_path,
            "Missing Project Tasks",
            1,
            "Project record may be missing a Project Tasks section.",
            "Warning"
        )

    if "progress log" not in lower_text:
        add_issue(
            issues,
            relative_path,
            "Missing Progress Log",
            1,
            "Project record may be missing a Progress Log section.",
            "Warning"
        )


def check_duplicate_knowledge_ids(relative_path, text, issues):
    """Detect duplicate KNOW IDs inside the Knowledge Register."""
    filename = Path(relative_path).name

    if filename != "Knowledge_Register.md":
        return

    matches = re.findall(r"\bKNOW-\d{3}\b", text)
    counts = defaultdict(int)

    for match in matches:
        counts[match] += 1

    for knowledge_id, count in sorted(counts.items()):
        if count > 1:
            add_issue(
                issues,
                relative_path,
                "Duplicate Knowledge ID",
                1,
                f"{knowledge_id} appears {count} times in the Knowledge Register.",
                "Error"
            )


def scan_markdown_file(path):
    """Run all checks on one Markdown file."""
    issues = []
    text = read_file(path)
    lines = text.splitlines()
    relative_path = path.relative_to(REPO_ROOT)

    check_unclosed_code_blocks(relative_path, lines, issues)
    check_broken_tables(relative_path, lines, issues)
    check_missing_document_information(relative_path, text, issues)
    check_status_field(relative_path, text, issues)
    check_empty_or_short_file(relative_path, lines, issues)
    check_project_record_completeness(relative_path, text, issues)
    check_duplicate_knowledge_ids(relative_path, text, issues)

    return issues


def find_markdown_files():
    """Find Markdown files in the repository."""
    markdown_files = []

    for path in REPO_ROOT.rglob("*.md"):
        if should_skip_path(path):
            continue

        markdown_files.append(path)

    return sorted(markdown_files)


def print_report(all_issues, scanned_count):
    """Print the audit report."""
    print("Markdown Audit Tool v0.1")
    print("=" * 60)
    print(f"Repository: {REPO_ROOT}")
    print(f"Markdown files scanned: {scanned_count}")
    print(f"Issues found: {len(all_issues)}")
    print("=" * 60)
    print()

    if not all_issues:
        print("No issues found.")
        return

    grouped = defaultdict(list)

    for issue in all_issues:
        grouped[issue["file_path"]].append(issue)

    for file_path, issues in grouped.items():
        print(file_path)
        print("-" * len(file_path))

        for issue in issues:
            print(f"[{issue['severity']}] {issue['issue_type']}")
            print(f"Line: {issue['line_number']}")
            print(f"Message: {issue['message']}")
            print()

        print()

    summary = defaultdict(int)

    for issue in all_issues:
        summary[issue["severity"]] += 1

    print("=" * 60)
    print("Summary by severity")
    print("=" * 60)
    print(f"Errors: {summary['Error']}")
    print(f"Warnings: {summary['Warning']}")
    print(f"Info: {summary['Info']}")
    print()
    print("Note: This tool is read-only. It does not edit, delete, commit, or push files.")


def main():
    """Run the Markdown audit."""
    markdown_files = find_markdown_files()
    all_issues = []

    for path in markdown_files:
        all_issues.extend(scan_markdown_file(path))

    print_report(all_issues, len(markdown_files))


if __name__ == "__main__":
    main()