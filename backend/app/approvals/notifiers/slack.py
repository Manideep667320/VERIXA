"""Slack Block Kit approvals and request-signature verification."""
from __future__ import annotations

import hashlib
import hmac
import json
import time

import httpx

from app.approvals.notifiers.base import ApprovalNotice, NotifierError
from app.core.config import settings


def verify_slack_signature(
    raw_body: bytes,
    timestamp: str,
    signature: str,
    signing_secret: str,
    *,
    now: int | None = None,
    max_age_seconds: int = 300,
) -> bool:
    """Verify Slack's v0 HMAC-SHA256 signature and reject stale replayed requests."""
    if not signing_secret or not timestamp or not signature:
        return False
    try:
        request_time = int(timestamp)
    except ValueError:
        return False
    current_time = int(time.time()) if now is None else now
    if abs(current_time - request_time) > max_age_seconds:
        return False
    try:
        basestring = b"v0:" + timestamp.encode("ascii") + b":" + raw_body
        supplied = signature.encode("ascii")
    except UnicodeEncodeError:
        return False
    expected = ("v0=" + hmac.new(signing_secret.encode(), basestring, hashlib.sha256).hexdigest()).encode("ascii")
    return hmac.compare_digest(expected, supplied)


class SlackNotifier:
    channel = "slack"

    def __init__(self, *, bot_token: str | None = None, channel_id: str | None = None,
                 timeout_seconds: float = 10.0, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.bot_token = settings.slack_bot_token if bot_token is None else bot_token
        self.channel_id = settings.slack_approval_channel if channel_id is None else channel_id
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    async def send_approval(self, notice: ApprovalNotice) -> None:
        if not self.bot_token or not self.channel_id:
            raise NotifierError("Slack approval requires SLACK_BOT_TOKEN and SLACK_APPROVAL_CHANNEL.")
        payload = {
            "channel": self.channel_id,
            "text": f"Approval required for {notice.approval_id} ({notice.role})",
            "blocks": build_approval_blocks(notice),
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, transport=self.transport) as client:
                response = await client.post(
                    "https://slack.com/api/chat.postMessage", json=payload,
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                )
        except httpx.TimeoutException as exc:
            raise NotifierError("Slack approval message timed out.") from exc
        except httpx.HTTPError as exc:
            raise NotifierError(f"Slack approval message failed: {exc}") from exc
        if response.is_error:
            raise NotifierError(f"Slack returned HTTP {response.status_code} while posting approval.")
        try:
            result = response.json()
        except ValueError as exc:
            raise NotifierError("Slack returned invalid JSON while posting approval.") from exc
        if not result.get("ok"):
            raise NotifierError(f"Slack rejected approval message: {result.get('error', 'unknown_error')}")


def build_approval_blocks(notice: ApprovalNotice) -> list[dict]:
    value = json.dumps({"approval_id": notice.approval_id, "role": notice.role}, separators=(",", ":"))
    expiration = notice.expires_at.isoformat() if notice.expires_at else "No active timeout"
    return [
        {"type": "header", "text": {"type": "plain_text", "text": "Approval required"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Approval:* {notice.approval_id}"},
            {"type": "mrkdwn", "text": f"*Assigned role:* {notice.role}"},
            {"type": "mrkdwn", "text": f"*Risk:* {notice.risk_level}"},
            {"type": "mrkdwn", "text": f"*Amount:* ${notice.amount:,.2f}"},
        ]},
        {"type": "section", "text": {"type": "mrkdwn", "text":
          f"*Request:* {notice.request}\n*Action:* {notice.action_type} — {notice.action_reason}"}},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Decision deadline: {expiration}"}]},
        {"type": "actions", "elements": [
            {"type": "button", "action_id": "e2a_approve", "text": {"type": "plain_text", "text": "Approve"},
             "style": "primary", "value": value},
            {"type": "button", "action_id": "e2a_reject", "text": {"type": "plain_text", "text": "Reject"},
             "style": "danger", "value": value},
        ]},
    ]
