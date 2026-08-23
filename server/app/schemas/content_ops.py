from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class ContentPublishPackageCreate(BaseModel):
    productKey: Literal["shenlun", "theory"]
    templateId: str
    sourceType: str = Field(min_length=1, max_length=32)
    sourceId: str = Field(min_length=1, max_length=32)
    sourceTitle: str = ""
    campaignKey: str = ""
    deepLink: str = ""
    variants: dict[str, dict[str, Any]] = Field(default_factory=dict)
    plannedAt: datetime | None = None


class ContentPublishStatusBody(BaseModel):
    status: Literal["draft", "teaching_review", "ops_review", "ready", "published", "rejected"]
    reviewNote: str = ""


class ContentPublishPackageUpdate(BaseModel):
    sourceTitle: str | None = None
    campaignKey: str | None = None
    deepLink: str | None = None
    variants: dict[str, dict[str, Any]] | None = None
    plannedAt: datetime | None = None
