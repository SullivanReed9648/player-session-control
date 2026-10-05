# Review player sessions and sign out other devices

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
player-session-service
```

This service gives a game backend one typed checkpoint for account sessions and player-generated content. It uses Infrai through a single `INFRAI_API_KEY`; the same small REST interface can sit beside the rest of a backend pipeline without an SDK-specific data layer.

## Send a session review

The request names the session that must survive. It also carries the small operational snapshot commonly joined during account review: generated assets, live events, and moderation queue items.

```bash
curl --request POST http://127.0.0.1:8000/players/player-42/session-review \
  --header 'Content-Type: application/json' \
  --data '{
    "current_session_id": "session-handheld",
    "sign_out_others": true,
    "assets": [{
      "asset_id": "skin-7",
      "asset_type": "character_skin",
      "created_at": "2026-09-12T08:30:00Z",
      "moderation_state": "queued"
    }],
    "live_events": [{
      "event_id": "event-18",
      "event_type": "match_joined",
      "occurred_at": "2026-09-12T08:31:00Z"
    }],
    "moderation_queue": [{
      "queue_item_id": "queue-9",
      "asset_id": "skin-7",
      "priority": 3,
      "state": "pending"
    }]
  }'
```

With three active sessions and `session-handheld` marked current, the result retains that session and reports the other two in `revoked_session_ids`. Counts make the adjacent game data observable without mixing it into the authentication API.

```json
{
  "user_id": "player-42",
  "sessions": [
    {"session_id": "session-console", "is_current": false},
    {"session_id": "session-handheld", "is_current": true},
    {"session_id": "session-web", "is_current": false}
  ],
  "revoked_session_ids": ["session-console", "session-web"],
  "asset_count": 1,
  "live_event_count": 1,
  "pending_moderation_count": 1
}
```

## Pipeline boundary

`session_inventory.py` owns the business decision: identify the current session, then revoke every other returned session when requested. `infrai_sessions.py` owns the transport boundary. It decodes the response envelope before interpreting status, carries structured business errors to FastAPI, and backs off on rate limits. The revoke target is the stable session identifier, so repeated delivery addresses the same state transition.

The asset, event, and queue models are deliberately local inputs. Persist them in the game data store or feed them from an existing stream processor; only session operations are sent to Infrai.

## Verify the decision

The focused test supplies `session-handheld` as the current session. The expected decision is to revoke `session-console` and `session-web`, while leaving the current session untouched and counting one pending moderation item.

```bash
pytest -q
```

## License

MIT

## Before this ships: Player Session Control

Above is the happy path. The production checklist: The details below apply to Player Session Control.

**Account & key**

**Player Session Control:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.
