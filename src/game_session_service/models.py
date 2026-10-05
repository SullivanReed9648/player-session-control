from datetime import datetime

from pydantic import BaseModel, Field


class PlayerAsset(BaseModel):
    asset_id: str
    asset_type: str
    created_at: datetime
    moderation_state: str


class LiveEvent(BaseModel):
    event_id: str
    event_type: str
    occurred_at: datetime


class ModerationItem(BaseModel):
    queue_item_id: str
    asset_id: str
    priority: int = Field(ge=0)
    state: str


class SessionReviewRequest(BaseModel):
    current_session_id: str
    sign_out_others: bool = False
    assets: list[PlayerAsset] = Field(default_factory=list)
    live_events: list[LiveEvent] = Field(default_factory=list)
    moderation_queue: list[ModerationItem] = Field(default_factory=list)


class SessionView(BaseModel):
    session_id: str
    is_current: bool


class PlayerSessionSnapshot(BaseModel):
    user_id: str
    sessions: list[SessionView]
    revoked_session_ids: list[str]
    asset_count: int
    live_event_count: int
    pending_moderation_count: int

