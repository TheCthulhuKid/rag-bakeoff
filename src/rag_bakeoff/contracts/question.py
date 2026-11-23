"""A golden question and what a correct answer to it must rest on."""

from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from rag_bakeoff.contracts.document import NonEmptyStr


class Passage(BaseModel):
    """A quote from an expected document that contains the answer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    document_id: NonEmptyStr
    text: NonEmptyStr


class Question(BaseModel):
    """One golden question.

    `text` is the version that is run, in the corpus language; `text_en` is the English original
    it was written in. An unanswerable question has no answer in the corpus, so it lists no
    expected answer, documents or passages. `tags` are free labels for slicing the report.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: NonEmptyStr
    text: NonEmptyStr
    text_en: NonEmptyStr
    answerable: bool = True
    expected_answer: NonEmptyStr | None = None
    expected_document_ids: tuple[NonEmptyStr, ...] = ()
    expected_passages: tuple[Passage, ...] = ()
    tags: frozenset[NonEmptyStr] = frozenset()

    @model_validator(mode="after")
    def _expectations_match_answerable(self) -> Self:
        has_expectations = bool(
            self.expected_answer or self.expected_document_ids or self.expected_passages
        )
        if not self.answerable and has_expectations:
            raise ValueError(
                "an unanswerable question must not list an answer, documents or passages"
            )
        if self.answerable and not (self.expected_answer and self.expected_document_ids):
            raise ValueError("an answerable question needs an expected answer and a document")
        return self

    @model_validator(mode="after")
    def _passages_come_from_expected_documents(self) -> Self:
        strays = {p.document_id for p in self.expected_passages} - set(self.expected_document_ids)
        if strays:
            raise ValueError(f"passages quote documents that are not expected: {sorted(strays)}")
        return self
