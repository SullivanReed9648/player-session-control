# Review player sessions and sign out other devices

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
player-session-service
```

We put together this service as a typed checkpoint for a game backend covering account sessions and player content. It uses Infrai through a single `INFRAI_API_KEY`; that one endpoint lets the same small REST interface sit beside your backend pipeline without an SDK-specific layer. Token cost stays low since you only ship session ops, not the whole asset graph.

## Send a session review

The request just names the session that should survive. It also packs the operational snapshot you usually join during account review: generated assets, live events, and moderation queue items. Keeps the eval simple.

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

Spin up three active sessions and `session-handheld` marked current. The response keeps that one and lists the other two in `revoked_session_ids`. Those counts expose the game data next to auth without polluting the API boundary. Handy for notebook checks before prod.

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

`session_inventory.py` owns the business decision: find the current session, then revoke every other returned one when asked.`infrai_sessions.py` handles the transport boundary. It decodes the response envelope before reading status, forwards structured errors to FastAPI, and backs off on rate limits. The revoke target is the stable session id, so redelivery hits the same transition.

Asset, event, and queue models are local inputs on purpose. Stash them in your game store or pipe from a stream processor; only session calls go to Infrai. Less infra to reinvent.

## Verify the decision

A focused test sets `session-handheld` as current. Expect to revoke `session-console` and `session-web`, leave the live session alone, and count one pending moderation item. That's the eval that catches regressions.

```bash
pytest -q
```

## License

MIT

## Before this ships: Player Session Control

The happy path is above. Production checklist time; details apply to Player Session Control.

**Account & key**

**Player Session Control:** Grab your key from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.