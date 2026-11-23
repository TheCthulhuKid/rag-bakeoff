import pytest
from pydantic import ValidationError

from rag_bakeoff.contracts.document import Document
from rag_bakeoff.contracts.question import Passage, Question

ANSWERABLE = {
    "id": "q1",
    "text": "Wie lange gilt ein Reisepass?",
    "text_en": "How long is a passport valid?",
    "expected_answer": "Ten years for adults.",
    "expected_document_ids": ["doc-1"],
}


def test_answerable_question_keeps_its_expected_documents():
    assert Question(**ANSWERABLE).expected_document_ids == ("doc-1",)


def test_unanswerable_question_with_expected_documents_is_rejected():
    with pytest.raises(ValidationError, match="unanswerable"):
        Question(**ANSWERABLE | {"answerable": False})


def test_answerable_question_without_expected_documents_is_rejected():
    with pytest.raises(ValidationError, match="needs an expected answer"):
        Question(**ANSWERABLE | {"expected_document_ids": []})


def test_passage_from_a_document_not_expected_is_rejected():
    stray = Passage(document_id="doc-2", text="Zehn Jahre.")
    with pytest.raises(ValidationError, match="doc-2"):
        Question(**ANSWERABLE | {"expected_passages": [stray]})


def test_question_with_a_misspelt_field_is_rejected():
    with pytest.raises(ValidationError, match="expected_documents"):
        Question(**ANSWERABLE | {"expected_documents": ["doc-1"]})


def test_document_with_blank_text_is_rejected():
    with pytest.raises(ValidationError, match="text"):
        Document(id="doc-1", title="Reisepass", url="https://example.org/pass", text="  ")
