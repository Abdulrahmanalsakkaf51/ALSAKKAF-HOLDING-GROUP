import json
from pathlib import Path


DATA_FILE = Path(__file__).with_name("knowledge_map.json")


def load_knowledge_map():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing knowledge map: {DATA_FILE}")

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def score_entry(question, entry):
    question_lower = question.lower()
    score = 0

    for keyword in entry.get("keywords", []):
        keyword_lower = keyword.lower()
        if keyword_lower in question_lower:
            score += len(keyword_lower)

    return score


def find_best_entry(question, entries):
    best_entry = None
    best_score = 0

    for entry in entries:
        score = score_entry(question, entry)

        if score > best_score:
            best_score = score
            best_entry = entry

    return best_entry


def format_answer(entry):
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
""".strip()


def missing_answer(question):
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

Question Asked:
{question}
""".strip()


def main():
    data = load_knowledge_map()
    entries = data.get("entries", [])

    print("=" * 60)
    print("ALSAKKAF HOLDING GROUP — Librarian Tool v0.1")
    print("PARTNER-001 — The Librarian")
    print("=" * 60)
    print("Type your question below.")
    print("Type 'exit' to close.")
    print()

    while True:
        question = input("Ask The Librarian: ").strip()

        if question.lower() in ["exit", "quit", "close"]:
            print("The Librarian session is closed.")
            break

        if not question:
            print("Please type a question.")
            continue

        entry = find_best_entry(question, entries)

        print()
        print("-" * 60)

        if entry:
            print(format_answer(entry))
        else:
            print(missing_answer(question))

        print("-" * 60)
        print()


if __name__ == "__main__":
    main()