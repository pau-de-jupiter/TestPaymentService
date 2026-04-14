import asyncio
import random
import logging

logger = logging.getLogger(__name__)

SUCCESS_RATE = 0.9
MIN_PROCESSING_TIME = 2
MAX_PROCESSING_TIME = 5


async def process_payment(payment_id: str) -> bool:
    '''Эмуляция внешнего платежного шлюза.

    Returns:
        True  — платеж успешен (90%)
        False — платеж отклонен (10%)
    '''
    delay = random.uniform(MIN_PROCESSING_TIME, MAX_PROCESSING_TIME)
    await asyncio.sleep(delay)

    success = random.random() < SUCCESS_RATE
    logger.info(
        'Gateway processed payment_id=%s result=%s delay=%.2fs',
        payment_id, 'succeeded' if success else 'failed', delay,
    )
    return success
