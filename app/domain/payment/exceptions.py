from app.domain.exceptions import NotFoundError, AlreadyExistsError


class PaymentNotFound(NotFoundError):
    def __init__(self, payment_id: str) -> None:
        super().__init__(f'Payment with id={payment_id} not found')


class DuplicateIdempotencyKey(AlreadyExistsError):
    def __init__(self, key: str) -> None:
        super().__init__(f'Payment with idempotency_key={key} already exists')
