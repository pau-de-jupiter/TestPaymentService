from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetPaymentById:
    """DTO для получения платежа по ID."""
    payment_id: UUID
