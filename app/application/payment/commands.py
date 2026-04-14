from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from app.domain.payment.value_objects import Currency, PaymentStatus


@dataclass(frozen=True)
class CommandCreatePayment:
    """DTO для создания платежа."""
    idempotency_key: str
    amount: Decimal
    currency: Currency
    description: str
    webhook_url: str
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CommandCreateOutboxEvent:
    """DTO для создания события в Outbox."""
    payment_id: UUID
    payload: dict


@dataclass(frozen=True)
class CommandUpdatePaymentStatus:
    """DTO для обновления статуса платежа."""
    payment_id: UUID
    status: PaymentStatus
