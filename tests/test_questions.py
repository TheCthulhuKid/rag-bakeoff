import json

import pytest

from rag_bakeoff.cli import main
from rag_bakeoff.contracts.document import Document
from rag_bakeoff.corpus.loader import write_documents
from rag_bakeoff.corpus.questions import QuestionFileError, load_questions


def document(id, text="Der Reisepass gilt zehn Jahre."):
    return Document(id=id, title="Reisepass", url=f"https://example.org/{id}", text=text)


DOCUMENTS = [document("pass"), document("pass-copy"), document("visa", "Ein Visum gilt 90 Tage.")]


def question_file(tmp_path, *questions):
    base = {"text": "Wie lange?", "text_en": "How long?", "expected_answer": "Ten years."}
    path = tmp_path / "questions.jsonl"
    path.write_text("".join(json.dumps(base | question) + "\n" for question in questions))
    return path


def problems(tmp_path, *questions):
    with pytest.raises(QuestionFileError) as error:
        load_questions(question_file(tmp_path, *questions), DOCUMENTS)
    return error.value.problems


def test_question_pointing_at_an_unknown_document_is_rejected(tmp_path):
    question = {"id": "q1", "expected_document_ids": ["passport"]}
    assert problems(tmp_path, question) == ["q1: expects unknown document passport"]


def test_two_questions_with_the_same_id_are_rejected(tmp_path):
    question = {"id": "q1", "expected_document_ids": ["visa"]}
    assert problems(tmp_path, question, question) == ["q1: question ID is used more than once"]


def test_question_expecting_one_of_two_identical_documents_is_rejected(tmp_path):
    question = {"id": "q1", "expected_document_ids": ["pass"]}
    assert problems(tmp_path, question) == [
        "q1: must also expect pass-copy, which has the same text"
    ]


def test_every_problem_is_reported_with_its_line_or_question(tmp_path):
    misspelt = {"id": "q1", "expected_documents": ["visa"]}
    unknown = {"id": "q2", "expected_document_ids": ["passport"]}
    found = problems(tmp_path, misspelt, unknown)
    assert [problem.split(":")[0] for problem in found] == ["line 1", "q2"]


def test_check_questions_command_summarises_a_valid_file(tmp_path, capsys):
    write_documents(DOCUMENTS, tmp_path / "documents.jsonl")
    path = question_file(tmp_path, {"id": "q1", "expected_document_ids": ["pass", "pass-copy"]})
    main(["check-questions", str(path), "--documents", str(tmp_path / "documents.jsonl")])
    assert (
        "1 questions are valid: 1 answerable (1 with several documents)" in capsys.readouterr().out
    )


def test_check_questions_command_fails_and_lists_the_problems(tmp_path, capsys):
    write_documents(DOCUMENTS, tmp_path / "documents.jsonl")
    path = question_file(tmp_path, {"id": "q1", "expected_document_ids": ["passport"]})
    with pytest.raises(SystemExit):
        main(["check-questions", str(path), "--documents", str(tmp_path / "documents.jsonl")])
    assert "q1: expects unknown document passport" in capsys.readouterr().out
