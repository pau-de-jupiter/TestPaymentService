from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.domain.payment.value_objects import Currency, PaymentStatus


@dataclass
class Payment:
    id: UUID
    idempotency_key: str
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict
    status: PaymentStatus
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None
