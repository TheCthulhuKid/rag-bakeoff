"""Read a golden question file and check it against the corpus."""

from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path

from pydantic import ValidationError

from rag_bakeoff.contracts.document import Document
from rag_bakeoff.contracts.question import Question


class QuestionFileError(ValueError):
    """Lists every problem found in a question file, so they can be fixed in one pass."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


def load_questions(path: Path, documents: Sequence[Document]) -> list[Question]:
    """Return the questions in a JSONL file, or raise QuestionFileError naming all problems.

    Beyond the rules of the Question contract, question IDs must be unique and every expected
    document must exist. Where the corpus holds the same text under several IDs, a question
    must expect all of them, as a retriever cannot tell them apart.
    """
    questions, problems = _parse(path)
    repeated = [id for id, count in Counter(q.id for q in questions).items() if count > 1]
    problems += [f"{id}: question ID is used more than once" for id in repeated]
    twins = _twins(documents)
    for question in questions:
        problems += _document_problems(question, twins)
    if problems:
        raise QuestionFileError(problems)
    return questions


def _parse(path: Path) -> tuple[list[Question], list[str]]:
    questions, problems = [], []
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            questions.append(Question.model_validate_json(line))
        except ValidationError as error:
            details = "; ".join(
                f"{'.'.join(map(str, e['loc'])) or 'question'}: {e['msg']}" for e in error.errors()
            )
            problems.append(f"line {number}: {details}")
    return questions, problems


def _twins(documents: Sequence[Document]) -> dict[str, set[str]]:
    """Map every document ID to the IDs that share its text, itself included."""
    by_text = defaultdict(set)
    for document in documents:
        by_text[document.text].add(document.id)
    return {id: ids for ids in by_text.values() for id in ids}


def _document_problems(question: Question, twins: dict[str, set[str]]) -> list[str]:
    expected = question.expected_document_ids
    problems = [f"expects unknown document {id}" for id in expected if id not in twins]
    if len(set(expected)) < len(expected):
        problems.append("lists a document more than once")
    missing = set().union(*(twins.get(id, set()) for id in expected)) - set(expected)
    problems += [f"must also expect {id}, which has the same text" for id in sorted(missing)]
    return [f"{question.id}: {problem}" for problem in problems]
