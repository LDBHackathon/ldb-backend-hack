from fastapi import APIRouter, Depends, status

from app.middlewares.ratelimiter import RateLimiter
from app.schemas.responses.generic import ErrorResponseSchema

from . import accounts, customers, health, hooks, webhooks

routes = APIRouter(
    dependencies=[Depends(RateLimiter)],
    responses={status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponseSchema}},
)

routes.include_router(health.router)
routes.include_router(customers.router)
routes.include_router(accounts.router)
routes.include_router(webhooks.router)
routes.include_router(hooks.router)
