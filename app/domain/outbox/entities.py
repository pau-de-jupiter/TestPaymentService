from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class OutboxEvent:
    id: UUID
    payment_id: UUID
    payload: dict
    published: bool
    failed: bool
    retry_count: int
    locked_until: datetime | None
