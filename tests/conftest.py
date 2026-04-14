from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.domain.payment.entities import Payment
from app.domain.payment.value_objects import Currency, PaymentStatus


@pytest.fixture
def payment_id():
    return uuid4()


@pytest.fixture
def sample_payment(payment_id):
    return Payment(
        id=payment_id,
        idempotency_key='test-key-001',
        amount=Decimal('100.00'),
        currency=Currency.RUB,
        description='Test payment',
        metadata={},
        status=PaymentStatus.PENDING,
        webhook_url='http://localhost/webhooks/',
        created_at=datetime.now(timezone.utc),
        processed_at=None,
    )


@pytest.fixture
def mock_payment_repo():
    return AsyncMock()


@pytest.fixture
def mock_outbox_repo():
    return AsyncMock()
