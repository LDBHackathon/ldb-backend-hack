from fastapi import APIRouter, Depends, status

from app.middlewares.ratelimiter import RateLimiter
from app.schemas.responses.generic import ErrorResponseSchema

from . import accounts, auth, customers, health, hooks, merchants, portal, v1, webhooks, webhooks_public

routes = APIRouter(
    dependencies=[Depends(RateLimiter)],
    responses={status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponseSchema}},
)

routes.include_router(health.router)
routes.include_router(auth.router)
routes.include_router(portal.router)
routes.include_router(v1.router)
routes.include_router(merchants.router)
routes.include_router(customers.router)
routes.include_router(accounts.router)
routes.include_router(webhooks.router)
routes.include_router(webhooks_public.router)
routes.include_router(hooks.router)
