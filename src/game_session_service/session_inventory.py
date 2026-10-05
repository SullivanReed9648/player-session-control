from typing import Any, Protocol

from .models import PlayerSessionSnapshot, SessionReviewRequest, SessionView


class SessionGateway(Protocol):
    async def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def revoke(self, session_id: str) -> None:
        raise NotImplementedError


async def review_player_sessions(
    gateway: SessionGateway,
    user_id: str,
    review: SessionReviewRequest,
) -> PlayerSessionSnapshot:
    records = await gateway.list_for_user(user_id)
    sessions = [
        SessionView(
            session_id=str(record["session_id"]),
            is_current=str(record["session_id"]) == review.current_session_id,
        )
        for record in records
    ]
    revoked: list[str] = []
    if review.sign_out_others:
        for session in sessions:
            if not session.is_current:
                await gateway.revoke(session.session_id)
                revoked.append(session.session_id)

    return PlayerSessionSnapshot(
        user_id=user_id,
        sessions=sessions,
        revoked_session_ids=revoked,
        asset_count=len(review.assets),
        live_event_count=len(review.live_events),
        pending_moderation_count=sum(
            item.state == "pending" for item in review.moderation_queue
        ),
    )
