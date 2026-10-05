import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request

from .infrai_sessions import InfraiError, InfraiSessionClient
from .models import PlayerSessionSnapshot, SessionReviewRequest
from .session_inventory import review_player_sessions


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    api_key = os.environ["INFRAI_API_KEY"]
    app.state.sessions = InfraiSessionClient(api_key)
    yield
    await app.state.sessions.close()


service = FastAPI(title="Player session control", lifespan=lifespan)


@service.post(
    "/players/{user_id}/session-review",
    response_model=PlayerSessionSnapshot,
)
async def session_review(
    user_id: str,
    review: SessionReviewRequest,
    request: Request,
) -> PlayerSessionSnapshot:
    try:
        return await review_player_sessions(request.app.state.sessions, user_id, review)
    except InfraiError as exc:
        status_code = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=status_code,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc


def run() -> None:
    uvicorn.run("game_session_service.session_admin:service", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run()

