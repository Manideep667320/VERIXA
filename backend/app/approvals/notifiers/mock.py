"""In-memory notifier used by the offline suite and local demos."""
from app.approvals.notifiers.base import ApprovalNotice


class MockNotifier:
    channel = "mock"

    def __init__(self) -> None:
        self.sent: list[ApprovalNotice] = []

    async def send_approval(self, notice: ApprovalNotice) -> None:
        self.sent.append(notice)
