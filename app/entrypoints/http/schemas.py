from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.domain.payment.value_objects import Currency, PaymentStatus


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2, description='Сумма платежа')
    currency: Currency
    description: str = Field(min_length=1, max_length=500)
    webhook_url: HttpUrl
    metadata: dict = Field(default_factory=dict)


class PaymentCreateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class PaymentDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    payment_id: UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict
    status: PaymentStatus
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None
