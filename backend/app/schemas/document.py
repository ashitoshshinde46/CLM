from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentVersionCreate(BaseModel):
    file_path: str
    changes_summary: str | None = None


class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    version_number: int
    file_path: str
    changes_summary: str | None
    created_by: int
    created_at: datetime


class ClauseCreate(BaseModel):
    name: str
    category: str | None = None
    content: str
    tags: list[str] | None = None


class ClauseUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    content: str | None = None
    tags: list[str] | None = None


class ClauseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str | None
    content: str
    tags: list[str] | None
    usage_count: int
    created_at: datetime


class ClauseGenerateRequest(BaseModel):
    template: str
    clause_ids: list[int]


class ClauseGenerateResponse(BaseModel):
    generated_document: str
