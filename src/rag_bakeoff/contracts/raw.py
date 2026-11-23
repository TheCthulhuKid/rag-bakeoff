"""The record of one fetched page in the raw corpus manifest."""

from pydantic import AwareDatetime, BaseModel, ConfigDict

from rag_bakeoff.contracts.document import NonEmptyStr


class RawPage(BaseModel):
    """One manifest line. `file` is relative to the raw directory; `sha256` is of the page body."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    url: NonEmptyStr
    file: NonEmptyStr
    fetched_at: AwareDatetime
    sha256: NonEmptyStr
