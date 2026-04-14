import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BASE_DELAY = 1.0


async def send_webhook(webhook_url: str, payload: dict) -> None:
    '''Отправка webhook с экспоненциальным retry
    Делаем 3 retry, если все попытки исчерпаны -- логируем и продолжаем
    (платеж уже обработан, webhook — best-effort)
    '''
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.post(webhook_url, json=payload)
                response.raise_for_status()
                logger.info(
                    'Webhook sent successfully: url=%s attempt=%d',
                    webhook_url, attempt,
                )
                return
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                if attempt == MAX_RETRIES:
                    logger.error(
                        'Webhook failed after %d attempts: url=%s error=%s',
                        MAX_RETRIES, webhook_url, exc,
                    )
                    return
                delay = BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    'Webhook attempt %d/%d failed, retrying in %.1fs: url=%s',
                    attempt, MAX_RETRIES, delay, webhook_url,
                )
                await asyncio.sleep(delay)
