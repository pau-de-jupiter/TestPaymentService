import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

from app.domain.exceptions import NotFoundError, AlreadyExistsError, BusinessLogicError
from app.infrastructure.broker.connection import broker, payments_exchange, payments_queue
from app.infrastructure.outbox.poller import run_outbox_poller
from app.entrypoints.http.endpoints.payments import router as payments_router
from app.entrypoints.http.endpoints.webhook import webhook_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await broker.connect()
    await broker.declare_exchange(payments_exchange)
    await broker.declare_queue(payments_queue)
    poller_task = asyncio.create_task(run_outbox_poller())
    try:
        yield
    finally:
        poller_task.cancel()
        await broker.close()


app = FastAPI(
    title='Payment Processing Service',
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

app.include_router(payments_router)
app.include_router(webhook_router)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> ORJSONResponse:
    return ORJSONResponse(status_code=404, content={'detail': str(exc)})


@app.exception_handler(AlreadyExistsError)
async def already_exists_handler(request: Request, exc: AlreadyExistsError) -> ORJSONResponse:
    return ORJSONResponse(status_code=409, content={'detail': str(exc)})


@app.exception_handler(BusinessLogicError)
async def business_logic_handler(request: Request, exc: BusinessLogicError) -> ORJSONResponse:
    return ORJSONResponse(status_code=400, content={'detail': str(exc)})
