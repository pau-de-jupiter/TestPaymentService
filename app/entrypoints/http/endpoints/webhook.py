import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
webhook_router = APIRouter(prefix='/webhooks', tags=['webhooks'])


@webhook_router.post('/', response_model=None)
async def test_webhook(request: Request) -> None:
    body = await request.body()
    logger.info('[WEBHOOK TEST] Arrived hook with body: %s', body)
