from enum import StrEnum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime as dt_datetime


class IsSpam(StrEnum):
    SPAM = "SPAM"
    NOT_SPAM = "NOT_SPAM"
    NOT_SURE = "NOT_SURE"


class CallClassification(BaseModel):
    is_spam: IsSpam
    reason_for_call: str


class CallMetadata(BaseModel):
    datetime: dt_datetime = Field(alias="datetime")
    call_duration: Optional[int] = Field(default=None, alias="callDuration")
    call_transcript: Optional[str] = Field(default=None, alias="callTranscript")
    reason_for_call: Optional[str] = Field(default=None, alias="reasonForCall")
    is_spam: Optional[IsSpam] = Field(default=None, alias="isSpam")

    model_config = {"populate_by_name": True}
