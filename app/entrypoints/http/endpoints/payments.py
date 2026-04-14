from uuid import UUID

from fastapi import APIRouter, Depends, Header, status

from app.application.payment.commands import CommandCreatePayment
from app.application.payment.queries import GetPaymentById
from app.application.payment.service import PaymentService
from app.dependency import get_payment_service
from app.entrypoints.http.dependencies import verify_api_key
from app.entrypoints.http.schemas import PaymentCreateRequest, PaymentCreateResponse, PaymentDetailResponse

router = APIRouter(
    prefix='/api/v1/payments',
    tags=['payments'],
    dependencies=[Depends(verify_api_key)],
)


@router.post(
    '/',
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_payment(
    request: PaymentCreateRequest,
    idempotency_key: str = Header(..., alias='Idempotency-Key'),
    service: PaymentService = Depends(get_payment_service),
) -> PaymentCreateResponse:
    command = CommandCreatePayment(
        idempotency_key=idempotency_key,
        amount=request.amount,
        currency=request.currency,
        description=request.description,
        webhook_url=str(request.webhook_url),
        metadata=request.metadata,
    )
    payment = await service.create_payment(data=command)
    return PaymentCreateResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )


@router.get(
    '/{payment_id}',
    response_model=PaymentDetailResponse,
)
async def get_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service),
) -> PaymentDetailResponse:
    query = GetPaymentById(payment_id=payment_id)
    payment = await service.get_payment(query=query)
    return PaymentDetailResponse(
        payment_id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.metadata,
        status=payment.status,
        webhook_url=payment.webhook_url,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
    )
