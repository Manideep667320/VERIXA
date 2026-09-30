"""SMTP approval notifications with signed, expiring, single-use action links."""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import smtplib
import time
from email.message import EmailMessage
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from app.approvals.notifiers.base import ApprovalNotice, NotifierError
from app.core.config import settings


class EmailActionTokenError(ValueError):
    """A signed email approval link is malformed, forged, or expired."""


class ExpiredEmailActionToken(EmailActionTokenError):
    """A signed email approval link is outside its allowed lifetime."""


class EmailAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    decision: Literal["approve", "reject"]
    role: str
    recipient: str
    expires_at: int
    nonce: str


def sign_email_action(
    approval_id: str,
    decision: Literal["approve", "reject"],
    role: str,
    recipient: str,
    *,
    expires_at: int,
    secret: str | None = None,
) -> str:
    signing_key = settings.approval_link_secret if secret is None else secret
    if not signing_key:
        raise NotifierError("Email approval links require APPROVAL_LINK_SECRET.")
    payload = EmailAction(approval_id=approval_id, decision=decision, role=role,
                          recipient=recipient, expires_at=expires_at, nonce=uuid4().hex)
    encoded = _b64encode(json.dumps(payload.model_dump(), sort_keys=True, separators=(",", ":")).encode())
    signature = hmac.new(signing_key.encode(), encoded.encode("ascii"), hashlib.sha256).digest()
    return f"{encoded}.{_b64encode(signature)}"


def verify_email_action(token: str, *, now: int | None = None, secret: str | None = None) -> EmailAction:
    signing_key = settings.approval_link_secret if secret is None else secret
    if not signing_key:
        raise EmailActionTokenError("Email approval link verification is not configured.")
    try:
        encoded, supplied_signature = token.split(".", maxsplit=1)
        expected = hmac.new(signing_key.encode(), encoded.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64decode(supplied_signature)):
            raise EmailActionTokenError("Email approval link signature is invalid.")
        payload = EmailAction.model_validate_json(_b64decode(encoded))
    except EmailActionTokenError:
        raise
    except Exception as exc:
        raise EmailActionTokenError("Email approval link is malformed.") from exc
    if payload.expires_at <= (int(time.time()) if now is None else now):
        raise ExpiredEmailActionToken("Email approval link has expired.")
    return payload


class EmailNotifier:
    channel = "email"

    def __init__(self, *, recipients: dict[str, list[str]] | None = None, smtp_host: str | None = None,
                 smtp_port: int | None = None, username: str | None = None, password: str | None = None,
                 sender: str | None = None, base_url: str | None = None, secret: str | None = None) -> None:
        self.recipients = settings.approval_role_email_recipients if recipients is None else recipients
        self.smtp_host = settings.smtp_host if smtp_host is None else smtp_host
        self.smtp_port = settings.smtp_port if smtp_port is None else smtp_port
        self.username = settings.smtp_username if username is None else username
        self.password = settings.smtp_password if password is None else password
        self.sender = settings.smtp_from_email if sender is None else sender
        self.base_url = settings.approval_public_base_url.rstrip("/") if base_url is None else base_url.rstrip("/")
        self.secret = settings.approval_link_secret if secret is None else secret

    async def send_approval(self, notice: ApprovalNotice) -> None:
        recipients = self.recipients.get(notice.role, [])
        if not recipients:
            raise NotifierError(f"No email recipient configured for approval role: {notice.role}")
        if not self.smtp_host or not self.sender or not self.secret:
            raise NotifierError("Email approvals require SMTP_HOST, SMTP_FROM_EMAIL, and APPROVAL_LINK_SECRET.")
        expiry = int(notice.expires_at.timestamp()) if notice.expires_at else int(time.time()) + 86400
        for recipient in recipients:
            approve_url = self._link(notice, "approve", recipient, expiry)
            reject_url = self._link(notice, "reject", recipient, expiry)
            message = EmailMessage()
            message["Subject"] = f"Approval required: {notice.approval_id} ({notice.role})"
            message["From"] = self.sender
            message["To"] = recipient
            message.set_content(
                f"Approval: {notice.approval_id}\nRole: {notice.role}\n"
                f"Request: {notice.request}\nAction: {notice.action_type} — {notice.action_reason}\n"
                f"Risk: {notice.risk_level}; amount: ${notice.amount:,.2f}\n\n"
                f"Approve: {approve_url}\nReject: {reject_url}\n"
                "Links expire and can only decide this approval once."
            )
            await asyncio.to_thread(self._send, message)

    def _link(self, notice: ApprovalNotice, decision: Literal["approve", "reject"],
              recipient: str, expiry: int) -> str:
        token = sign_email_action(notice.approval_id, decision, notice.role, recipient,
                                  expires_at=expiry, secret=self.secret)
        return f"{self.base_url}/api/approvals/email/{token}"

    def _send(self, message: EmailMessage) -> None:
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.starttls()
                if self.username:
                    server.login(self.username, self.password)
                server.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            raise NotifierError(f"Approval email delivery failed: {exc}") from exc


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
