import asyncio
from typing import Any

from game_session_service.models import SessionReviewRequest
from game_session_service.session_inventory import review_player_sessions


class RecordingGateway:
    def __init__(self) -> None:
        self.revoked: list[str] = []

    async def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        assert user_id == "player-42"
        return [
            {"session_id": "session-console"},
            {"session_id": "session-handheld"},
            {"session_id": "session-web"},
        ]

    async def revoke(self, session_id: str) -> None:
        self.revoked.append(session_id)


def test_sign_out_others_preserves_current_session() -> None:
    gateway = RecordingGateway()
    review = SessionReviewRequest(
        current_session_id="session-handheld",
        sign_out_others=True,
        moderation_queue=[
            {
                "queue_item_id": "queue-9",
                "asset_id": "skin-7",
                "priority": 3,
                "state": "pending",
            }
        ],
    )

    result = asyncio.run(review_player_sessions(gateway, "player-42", review))

    assert gateway.revoked == ["session-console", "session-web"]
    assert result.revoked_session_ids == ["session-console", "session-web"]
    assert result.pending_moderation_count == 1

