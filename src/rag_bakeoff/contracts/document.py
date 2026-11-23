"""The normalised form of one corpus page."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Document(BaseModel):
    """One corpus page after loading. `metadata` holds source details such as owner and date."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: NonEmptyStr
    title: NonEmptyStr
    url: NonEmptyStr
    text: NonEmptyStr
    metadata: dict[str, str] = {}
