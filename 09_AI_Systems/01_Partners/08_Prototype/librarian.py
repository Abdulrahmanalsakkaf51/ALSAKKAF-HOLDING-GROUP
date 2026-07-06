import json
import re
from pathlib import Path


DATA_FILE = Path(__file__).with_name("knowledge_map.json")
REPO_ROOT = Path(__file__).resolve().parents[3]
MIN_MATCH_SCORE = 5

STOPWORDS = {
    "what", "is", "the", "a", "an", "of", "to", "do", "does", "did",
    "me", "about", "something", "not", "yet", "where", "which", "when",
    "how", "are", "and", "or", "in", "on", "for", "with", "be", "was",
    "were", "this", "that", "tell"
}

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules"
}


def load_knowledge_map():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing knowledge map: {DATA_FILE}")

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\- ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text):
    words = normalize_text(text).split()
    return {word for word in words if word not in STOPWORDS and len(word) > 1}


def score_keyword(question_normalized, question_tokens, keyword):
    keyword_normalized = normalize_text(keyword)
    keyword_tokens = tokenize(keyword)

    if not keyword_normalized or not keyword_tokens:
        return 0

    score = 0

    if keyword_normalized in question_normalized:
        score += len(keyword_tokens) * 5

    shared_tokens = question_tokens.intersection(keyword_tokens)
    score += len(shared_tokens) * 2

    if re.search(r"[a-z]+-\d+", keyword_normalized):
        if keyword_normalized in question_normalized:
            score += 10

    return score


def score_entry(question, entry):
    question_normalized = normalize_text(question)
    question_tokens = tokenize(question)

    if not question_tokens:
        return 0

    keyword_scores = []

    for keyword in entry.get("keywords", []):
        keyword_scores.append(
            score_keyword(question_normalized, question_tokens, keyword)
        )

    if not keyword_scores:
        return 0

    return max(keyword_scores)


def find_best_entry(question, entries):
    scored_entries = []

    for entry in entries:
        score = score_entry(question, entry)
        scored_entries.append((score, entry))

    scored_entries.sort(key=lambda item: item[0], reverse=True)

    if not scored_entries:
        return None, 0, []

    best_score, best_entry = scored_entries[0]

    if best_score < MIN_MATCH_SCORE:
        return None, best_score, scored_entries[:5]

    return best_entry, best_score, scored_entries[:5]


def format_answer(entry, score):
    related_sources = entry.get("related_sources", [])

    if related_sources:
        related_text = "\n".join(f"- {source}" for source in related_sources)
    else:
        related_text = "None listed."

    return f"""
Answer:
{entry.get("answer", "No answer available.")}

Primary Source:
{entry.get("primary_source", "Missing")}

Related Sources:
{related_text}

Status:
{entry.get("status", "Needs Review")}

Recommended Action:
{entry.get("recommended_action", "Review the relevant AOS documents.")}

Match Score:
{score}
""".strip()


def format_suggestions(scored_entries):
    suggestions = []

    for score, entry in scored_entries:
        if score <= 0:
            continue

        keywords = entry.get("keywords", [])
        if keywords:
            suggestions.append(f"- {keywords[0]}")

    if not suggestions:
        return "No strong suggestions available."

    return "\n".join(suggestions)


def should_skip_path(path):
    return any(part in EXCLUDED_DIRS for part in path.parts)


def read_text_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def score_text_search(query, text):
    query_normalized = normalize_text(query)
    query_tokens = tokenize(query)
    text_normalized = normalize_text(text)

    if not query_tokens:
        return 0

    score = 0

    if query_normalized and query_normalized in text_normalized:
        score += 20

    for token in query_tokens:
        count = text_normalized.count(token)
        score += min(count, 10) * 2

    if re.search(r"[a-z]+-\d+", query_normalized):
        if query_normalized in text_normalized:
            score += 25

    return score


def find_best_line(query, lines):
    best_score = 0
    best_line_number = 1
    best_line = ""

    for index, line in enumerate(lines, start=1):
        score = score_text_search(query, line)

        if score > best_score:
            best_score = score
            best_line_number = index
            best_line = line.strip()

    return best_line_number, best_line, best_score


def search_markdown_files(query, limit=5):
    results = []

    for path in REPO_ROOT.rglob("*.md"):
        if should_skip_path(path):
            continue

        try:
            text = read_text_file(path)
        except OSError:
            continue

        file_score = score_text_search(query, text)

        if file_score <= 0:
            continue

        lines = text.splitlines()
        line_number, best_line, line_score = find_best_line(query, lines)

        relative_path = path.relative_to(REPO_ROOT)

        results.append({
            "path": str(relative_path),
            "score": file_score,
            "line_number": line_number,
            "best_line": best_line
        })

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]


def format_file_search_results(results):
    if not results:
        return """
File Search:
No matching Markdown files were found.
""".strip()

    output = ["File Search Results:"]

    for result in results:
        output.append("")
        output.append(f"- File: {result['path']}")
        output.append(f"  Line: {result['line_number']}")
        output.append(f"  Match Score: {result['score']}")
        if result["best_line"]:
            output.append(f"  Best Match: {result['best_line']}")

    return "\n".join(output)


def missing_answer(question, scored_entries):
    suggestions = format_suggestions(scored_entries)
    file_results = search_markdown_files(question)
    file_results_text = format_file_search_results(file_results)

    return f"""
Answer:
I could not find a strong match for this question in the current Librarian knowledge map.

Primary Source:
Missing

Related Sources:
None identified from the knowledge map.

Status:
Missing / Needs Review

Recommended Action:
Review the file search results below. If the knowledge exists, add it to the Librarian knowledge map or Knowledge Register. If it does not exist, document it before treating it as institutional knowledge.

Possible Related Topics:
{suggestions}

{file_results_text}

Question Asked:
{question}
""".strip()


def show_help():
    return """
Available example questions:

1. What is AOS?
2. Where is Digital DNA documented?
3. Where is The Mind defined?
4. What is the Partner Operating Model?
5. Which ADR approved the Partner Registry?
6. Where is the 30-Partner Company Cell explained?
7. What is The Librarian allowed to do?
8. What is The Librarian not allowed to do?
9. Which document should be updated when a new Partner is created?
10. Is The Librarian active, designed, proposed, or approved?

Commands:
- help
- search [word or phrase]
- exit

Examples:
search The Mind
search PRJ-001
search Partner Registry
""".strip()


def main():
    data = load_knowledge_map()
    entries = data.get("entries", [])

    print("=" * 60)
    print("ALSAKKAF HOLDING GROUP — Librarian Tool v0.4")
    print("PARTNER-001 — The Librarian")
    print("=" * 60)
    print("Type your question below.")
    print("Type 'help' to see example questions.")
    print("Type 'search [word or phrase]' to search Markdown files.")
    print("Type 'exit' to close.")
    print()

    while True:
        question = input("Ask The Librarian: ").strip()

        if question.lower() in ["exit", "quit", "close"]:
            print("The Librarian session is closed.")
            break

        if question.lower() == "help":
            print()
            print("-" * 60)
            print(show_help())
            print("-" * 60)
            print()
            continue

        if question.lower().startswith("search "):
            search_query = question[7:].strip()

            print()
            print("-" * 60)

            if not search_query:
                print("Please type something after 'search'.")
            else:
                results = search_markdown_files(search_query)
                print(format_file_search_results(results))

            print("-" * 60)
            print()
            continue

        if not question:
            print("Please type a question.")
            continue

        entry, score, scored_entries = find_best_entry(question, entries)

        print()
        print("-" * 60)

        if entry:
            print(format_answer(entry, score))
        else:
            print(missing_answer(question, scored_entries))

        print("-" * 60)
        print()


if __name__ == "__main__":
    main()