from enum import StrEnum
from datetime import datetime as dt_datetime
from pydantic import BaseModel, Field
from typing import Optional, TypedDict, Union


class InitiationMode(StrEnum):
    user_initiates = "User Initiates"
    ai_initiates_dynamic = "AI Initiates (Dynamic Message)"
    ai_initiates_defined = "AI Initiates (Defined Message)"


class SessionRequest(BaseModel):
    voiceModelName: str
    initiationMode: InitiationMode = InitiationMode.ai_initiates_dynamic
    knowledgeBaseTrigger: Optional[bool] = False
    initialMessage: Optional[str] = None
    instructions: Union[str, list[str]]


class SessionRequestDict(TypedDict):
    voiceModelName: str
    initiationMode: InitiationMode
    instructions: Union[str, list[str]]
    knowledgeBaseTrigger: Optional[bool]
    initialMessage: Optional[str]


class IsSpam(StrEnum):
    SPAM = "SPAM"
    NOT_SPAM = "NOT_SPAM"
    NOT_SURE = "NOT_SURE"


class AgentType(StrEnum):
    WEB_AGENT = "WEB_AGENT"
    PHONE_AGENT_TEST = "PHONE_AGENT_TEST"
    PHONE_AGENT_REGULAR = "PHONE_AGENT_REGULAR"


class CallbackRequired(StrEnum):
    YES = "YES"
    NO = "NO"
    NOT_SURE = "NOT_SURE"


class CalendarEvent(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class ServicePricing(BaseModel):
    name: Optional[str] = None
    price_from: Optional[int] = None
    price_to: Optional[int] = None


class CallClassification(BaseModel):
    is_spam: IsSpam
    reason_for_call: str
    callback_required: CallbackRequired
    callback_required_reason: str
    caller_name: Optional[str] = None
    calendar_event: Optional[CalendarEvent] = None
    service_pricing: Optional[ServicePricing] = None


class CallMetadata(BaseModel):
    datetime: dt_datetime = Field(alias="datetime")
    call_duration: Optional[int] = Field(default=None, alias="callDuration")
    call_transcript: Optional[str] = Field(default=None, alias="callTranscript")
    is_spam: Optional[IsSpam] = Field(default=None, alias="isSpam")
    reason_for_call: Optional[str] = Field(default=None, alias="reasonForCall")
    callback_required: Optional[CallbackRequired] = Field(default=None, alias="callbackRequired")
    callback_required_reason: Optional[str] = Field(default=None, alias="callbackRequiredReason")
    caller_name: Optional[str] = Field(default=None, alias="callerName")
    is_active: Optional[bool] = Field(default=None, alias="isActive")
    calendar_event: Optional[CalendarEvent] = Field(default=None, alias="calendarEvent")
    service_pricing: Optional[ServicePricing] = Field(default=None, alias="servicePricing")

    model_config = {"populate_by_name": True}
