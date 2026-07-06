import json
import re
from pathlib import Path


DATA_FILE = Path(__file__).with_name("knowledge_map.json")
MIN_MATCH_SCORE = 5

STOPWORDS = {
    "what", "is", "the", "a", "an", "of", "to", "do", "does", "did",
    "me", "about", "something", "not", "yet", "where", "which", "when",
    "how", "are", "and", "or", "in", "on", "for", "with", "be", "was",
    "were", "this", "that", "tell"
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

    # Strong score for exact phrase match
    if keyword_normalized in question_normalized:
        score += len(keyword_tokens) * 5

    # Medium score for meaningful shared words only
    shared_tokens = question_tokens.intersection(keyword_tokens)
    score += len(shared_tokens) * 2

    # Extra score for IDs like ADR-017, KNOW-024, POM-001
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

    # Use best keyword match, not total score.
    # This prevents weak repeated matches from creating false positives.
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


def missing_answer(question, scored_entries):
    suggestions = format_suggestions(scored_entries)

    return f"""
Answer:
I could not find a strong match for this question in the current Librarian knowledge map.

Primary Source:
Missing

Related Sources:
None identified.

Status:
Missing / Needs Review

Recommended Action:
Add this question or related knowledge to the Librarian Document Map, Knowledge Register, or the correct AOS source document before treating it as institutional knowledge.

Possible Related Topics:
{suggestions}

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
- exit
""".strip()


def main():
    data = load_knowledge_map()
    entries = data.get("entries", [])

    print("=" * 60)
    print("ALSAKKAF HOLDING GROUP — Librarian Tool v0.3")
    print("PARTNER-001 — The Librarian")
    print("=" * 60)
    print("Type your question below.")
    print("Type 'help' to see example questions.")
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