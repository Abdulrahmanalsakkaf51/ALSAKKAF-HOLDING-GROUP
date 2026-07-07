import json
import re
from pathlib import Path

DATA_FILE = Path(__file__).with_name("knowledge_map.json")
REPO_ROOT = Path(__file__).resolve().parents[3]
MIN_MATCH_SCORE = 5
MAX_FILE_RESULTS = 5

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "how", "i", "in", "is", "it", "me", "my", "of", "on",
    "or", "our", "please", "show", "tell", "that", "the", "this", "to",
    "us", "we", "what", "when", "where", "which", "who", "why", "with",
    "you", "your", "about"
}

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules"
}

TEST_INTENT_WORDS = {
    "test", "testing", "tests", "log", "logs", "prototype", "regression",
    "passed", "failed", "result", "results"
}

MISSING_KNOWLEDGE_PATTERNS = {
    "not documented yet",
    "not recorded yet",
    "not in the knowledge map",
    "not in knowledge map",
    "unknown topic",
    "something not documented",
    "something missing",
    "missing knowledge"
}




def load_knowledge_map():
    """Load the knowledge map safely."""
    if not DATA_FILE.exists():
        print(f"Error: knowledge map not found: {DATA_FILE}")
        return []

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        print(f"Error: knowledge_map.json is not valid JSON: {error}")
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if isinstance(data.get("entries"), list):
            return data["entries"]

        if isinstance(data.get("knowledge"), list):
            return data["knowledge"]

        entries = []
        for key, value in data.items():
            if isinstance(value, dict):
                item = dict(value)
                item.setdefault("topic", key)
                entries.append(item)
        return entries

    return []


def normalize_text(text):
    """Normalize text for matching."""
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def tokenize(text):
    """Convert text into useful search tokens."""
    words = re.findall(r"[a-zA-Z0-9_\-]+", normalize_text(text))
    return {word for word in words if word not in STOPWORDS and len(word) > 1}


def has_test_intent(query):
    """Detect if the user is intentionally searching for tests or logs."""
    return bool(tokenize(query).intersection(TEST_INTENT_WORDS))

def is_missing_knowledge_request(query):
    """Detect when the user is intentionally asking for missing/unknown knowledge."""
    query_norm = normalize_text(query)
    return any(pattern in query_norm for pattern in MISSING_KNOWLEDGE_PATTERNS)




def safe_list(value):
    """Return a clean list from a string/list/other value."""
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item) for item in value]

    if isinstance(value, str):
        return [value]

    return [str(value)]


def entry_text(entry):
    """Combine important entry fields for scoring."""
    parts = [
        entry.get("topic", ""),
        entry.get("title", ""),
        entry.get("question", ""),
        entry.get("answer", ""),
        entry.get("primary_source", ""),
        entry.get("source", ""),
        entry.get("status", ""),
        entry.get("recommended_action", "")
    ]

    parts.extend(safe_list(entry.get("keywords")))
    parts.extend(safe_list(entry.get("related_sources")))

    return " ".join(str(part) for part in parts if part)


def score_keyword(query, keyword):
    """Score one keyword against the query."""
    query_norm = normalize_text(query)
    keyword_norm = normalize_text(keyword)

    if not keyword_norm:
        return 0

    if query_norm == keyword_norm:
        return 20

    if query_norm in keyword_norm or keyword_norm in query_norm:
        return 12

    query_tokens = tokenize(query_norm)
    keyword_tokens = tokenize(keyword_norm)

    if not query_tokens or not keyword_tokens:
        return 0

    shared = query_tokens.intersection(keyword_tokens)
    return len(shared) * 5


def score_entry(query, entry):
    """Score a knowledge-map entry."""
    score = 0
    query_norm = normalize_text(query)
    query_tokens = tokenize(query)

    topic = normalize_text(entry.get("topic", entry.get("title", "")))
    if topic:
        if query_norm == topic:
            score += 25
        elif query_norm in topic or topic in query_norm:
            score += 15

    for keyword in safe_list(entry.get("keywords")):
        score += score_keyword(query, keyword)

    full_text = normalize_text(entry_text(entry))
    if query_norm and query_norm in full_text:
        score += 8

    entry_tokens = tokenize(full_text)
    shared = query_tokens.intersection(entry_tokens)
    score += len(shared) * 2

    return score


def find_best_entry(query, entries):
    """Find the best knowledge-map answer."""
    best_entry = None
    best_score = 0

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        score = score_entry(query, entry)
        if score > best_score:
            best_entry = entry
            best_score = score

    if best_entry is None or best_score < MIN_MATCH_SCORE:
        return None, best_score

    return best_entry, best_score


def format_sources(value):
    """Format source lists cleanly."""
    sources = safe_list(value)
    if not sources:
        return "None recorded"
    return ", ".join(sources)


def format_answer(entry, score):
    """Format a knowledge-map answer."""
    answer = entry.get("answer", "No answer recorded.")
    primary_source = entry.get("primary_source", entry.get("source", "No primary source recorded."))
    related_sources = entry.get("related_sources", [])
    status = entry.get("status", "No status recorded.")
    recommended_action = entry.get("recommended_action", "No recommended action recorded.")

    return f"""
Answer:
{answer}

Primary Source:
{primary_source}

Related Sources:
{format_sources(related_sources)}

Status:
{status}

Recommended Action:
{recommended_action}

Match Score:
{score}
""".strip()


def format_suggestions(entries):
    """Suggest available topics when no answer is found."""
    topics = []
    for entry in entries:
        if isinstance(entry, dict):
            topic = entry.get("topic") or entry.get("title")
            if topic:
                topics.append(str(topic))

    if not topics:
        return "No available topics found in knowledge_map.json."

    preview = topics[:10]
    return "\n".join(f"- {topic}" for topic in preview)


def should_skip_path(path):
    """Skip unwanted directories."""
    return any(part in EXCLUDED_DIRS for part in path.parts)


def read_text_file(path):
    """Read a Markdown file safely."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def score_text_search(query, text):
    """Score raw Markdown file content."""
    query_norm = normalize_text(query)
    query_tokens = tokenize(query)
    text_norm = normalize_text(text)
    text_tokens = tokenize(text)

    if not query_tokens:
        return 0

    score = 0

    if query_norm and query_norm in text_norm:
        score += 30

    shared = query_tokens.intersection(text_tokens)
    score += len(shared) * 8

    for token in query_tokens:
        occurrences = text_norm.count(token)
        score += min(occurrences, 10)

    return score


def find_best_line(query, text):
    """Find the best matching line in a Markdown file."""
    query_tokens = tokenize(query)
    best_line_number = 0
    best_line = ""
    best_score = 0

    for index, line in enumerate(text.splitlines(), start=1):
        line_norm = normalize_text(line)
        line_tokens = tokenize(line)

        if not line_tokens:
            continue

        score = len(query_tokens.intersection(line_tokens)) * 10

        if normalize_text(query) and normalize_text(query) in line_norm:
            score += 30

        if score > best_score:
            best_score = score
            best_line_number = index
            best_line = line.strip()

    return best_line_number, best_line, best_score


def get_path_priority(relative_path, query):
    """
    Rank official company sources above lower-priority notes/test logs.

    This is the main v0.5 improvement.
    """
    path_text = str(relative_path).replace("\\", "/").lower()
    filename = Path(relative_path).name.lower()
    test_intent = has_test_intent(query)

    priority = 0

    if filename == "knowledge_register.md":
        priority += 45

    if filename == "digital_dna.md":
        priority += 40

    if filename in {
        "company_constitution.md",
        "company_language_standard.md",
        "architecture_decision_log.md",
        "vision.md"
    }:
        priority += 35

    if "/01_governance/adr/" in path_text:
        priority += 30

    if filename in {
        "partner_registry.md",
        "project_register.md",
        "partner_operating_model.md",
        "partner_workforce_architecture.md",
        "project_operating_model.md"
    }:
        priority += 30

    if "/04_operations/01_project_records/" in path_text:
        priority += 28

    if "/01_partner_profiles/" in path_text:
        priority += 24

    if "/05_workflows/" in path_text:
        priority += 22

    if "/02_partner_prompts/" in path_text:
        priority += 12

    if "/07_aos_university/" in path_text:
        priority += 18

    if "/08_prototype/" in path_text:
        priority += 5

    is_test_log = (
        "/03_test_logs/" in path_text
        or "test_log" in filename
        or "test-log" in filename
        or "prototype_test_log" in filename
    )

    if is_test_log and test_intent:
        priority += 35
    elif is_test_log:
        priority -= 35

    return priority


def search_markdown_files(query, limit=MAX_FILE_RESULTS):
    """Search Markdown files and rank by content score + source priority."""
    results = []

    if not REPO_ROOT.exists():
        return results

    for path in REPO_ROOT.rglob("*.md"):
        if should_skip_path(path):
            continue

        text = read_text_file(path)
        if not text.strip():
            continue

        relative_path = path.relative_to(REPO_ROOT)
        content_score = score_text_search(query, text)

        if content_score <= 0:
            continue

        line_number, best_line, line_score = find_best_line(query, text)
        priority_score = get_path_priority(relative_path, query)
        total_score = content_score + priority_score + line_score

        if total_score < MIN_MATCH_SCORE:
            continue

        results.append({
            "path": str(relative_path),
            "line_number": line_number,
            "best_line": best_line,
            "content_score": content_score,
            "priority_score": priority_score,
            "line_score": line_score,
            "score": total_score
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]


def format_file_search_results(results):
    """Format Markdown search results."""
    if not results:
        return "No matching Markdown files found."

    lines = []
    for index, result in enumerate(results, start=1):
        lines.append(f"{index}. {result['path']}")
        lines.append(f"   Line: {result['line_number']}")
        lines.append(f"   Match Score: {result['score']}")
        lines.append(f"   Source Priority: {result['priority_score']}")
        lines.append(f"   Best Line: {result['best_line']}")
        lines.append("")

    return "\n".join(lines).strip()


def missing_answer(query, entries):
    """Return a safe missing-answer response with possible file matches."""
    file_results = search_markdown_files(query)

    return f"""
Answer:
I could not find a confirmed answer in the knowledge map.

Primary Source:
No confirmed primary source found in knowledge_map.json.

Related Sources:
Possible Markdown file matches:
{format_file_search_results(file_results)}

Status:
Missing / Needs Review

Recommended Action:
Review the possible file matches above. If one of them is correct, update knowledge_map.json or the relevant AOS record so The Librarian can answer this more confidently in the future.

Available Knowledge Map Topics:
{format_suggestions(entries)}
""".strip()


def show_help():
    """Show available commands."""
    return """
Available commands:

1. Ask a normal question
Example:
What is AOS?

2. Search Markdown files
Example:
search The Mind
search PRJ-001
search Librarian test

3. Show help
help

4. Exit
exit

Version:
The Librarian Tool v0.5

Main v0.5 Improvement:
Official company records are ranked above test logs unless the user is clearly searching for tests or logs.
""".strip()


def main():
    """Run the Librarian Tool."""
    entries = load_knowledge_map()

    print("The Librarian Tool v0.5")
    print("Type 'help' for commands or 'exit' to close.")
    print()

    while True:
        query = input("Ask The Librarian: ").strip()

        if not query:
            continue

        if query.lower() in {"exit", "quit"}:
            print("Closing The Librarian.")
            break

        if query.lower() == "help":
            print()
            print(show_help())
            print()
            continue

        if query.lower().startswith("search "):
            search_query = query[7:].strip()

            if not search_query:
                print("Please write what you want to search for after 'search'.")
                print()
                continue

            results = search_markdown_files(search_query)
            print()
            print("Markdown Search Results:")
            print(format_file_search_results(results))
            print()
            continue

        print()

        if is_missing_knowledge_request(query):
            print(missing_answer(query, entries))
            print()
            continue

        best_entry, score = find_best_entry(query, entries)

        if best_entry:
            print(format_answer(best_entry, score))
        else:
            print(missing_answer(query, entries))
        print()


if __name__ == "__main__":
    main()