from decimal import Decimal

import pytest

from app.application.payment.commands import CommandCreatePayment
from app.application.payment.queries import GetPaymentById
from app.application.payment.service import PaymentService
from app.domain.payment.exceptions import PaymentNotFound
from app.domain.payment.value_objects import Currency, PaymentStatus


@pytest.fixture
def service(mock_payment_repo, mock_outbox_repo):
    return PaymentService(
        payment_repo=mock_payment_repo,
        outbox_repo=mock_outbox_repo,
    )


@pytest.fixture
def create_command():
    return CommandCreatePayment(
        idempotency_key='test-key-001',
        amount=Decimal('100.00'),
        currency=Currency.RUB,
        description='Test payment',
        webhook_url='http://localhost/webhooks/',
        metadata={},
    )


@pytest.mark.asyncio
class TestCreatePayment:

    async def test_create_success(self, service, mock_payment_repo, mock_outbox_repo, sample_payment, create_command):
        mock_payment_repo.get_by_idempotency_key.return_value = None
        mock_payment_repo.create.return_value = sample_payment

        result = await service.create_payment(create_command)

        assert result.id == sample_payment.id
        assert result.status == PaymentStatus.PENDING
        mock_payment_repo.create.assert_called_once()
        mock_outbox_repo.create.assert_called_once()

    async def test_idempotency_returns_existing(self, service, mock_payment_repo, mock_outbox_repo, sample_payment, create_command):
        '''При повторном запросе с тем же ключом — возвращаем существующий платеж'''
        mock_payment_repo.get_by_idempotency_key.return_value = sample_payment

        result = await service.create_payment(create_command)

        assert result.id == sample_payment.id
        mock_payment_repo.create.assert_not_called()
        mock_outbox_repo.create.assert_not_called()

    async def test_outbox_event_created_with_correct_payload(self, service, mock_payment_repo, mock_outbox_repo, sample_payment, create_command):
        mock_payment_repo.get_by_idempotency_key.return_value = None
        mock_payment_repo.create.return_value = sample_payment

        await service.create_payment(create_command)

        outbox_call = mock_outbox_repo.create.call_args
        payload = outbox_call.kwargs['data'].payload
        assert payload['payment_id'] == str(sample_payment.id)
        assert payload['webhook_url'] == sample_payment.webhook_url


@pytest.mark.asyncio
class TestGetPayment:

    async def test_get_success(self, service, mock_payment_repo, sample_payment, payment_id):
        mock_payment_repo.get_by_id.return_value = sample_payment

        result = await service.get_payment(GetPaymentById(payment_id=payment_id))

        assert result.id == payment_id
        mock_payment_repo.get_by_id.assert_called_once()

    async def test_get_not_found(self, service, mock_payment_repo, payment_id):
        mock_payment_repo.get_by_id.return_value = None

        with pytest.raises(PaymentNotFound):
            await service.get_payment(GetPaymentById(payment_id=payment_id))
