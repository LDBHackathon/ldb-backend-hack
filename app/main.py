from contextlib import AsyncExitStack, asynccontextmanager
from collections.abc import AsyncIterator, Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app  # type: ignore
from secure import ContentSecurityPolicy, Secure

from app import __display_name__, __version__
from app.api import router
from app.bootstrap.merchants import bootstrap_default_merchant
from app.config.tortoise import register_orm
from app.jobs.nightly_reconciliation import run_nightly_reconciliation
from app.middlewares.metrics import MetricsMiddleware
from app.settings import settings


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(register_orm(app))
        await bootstrap_default_merchant()

        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            run_nightly_reconciliation,
            trigger="cron",
            hour=settings.NIGHTLY_RECONCILIATION_HOUR,
            minute=0,
            id="nightly_reconciliation",
            replace_existing=True,
        )
        scheduler.start()

        yield
        scheduler.shutdown(wait=False)


application = FastAPI(
    title=__display_name__,
    version=__version__,
    lifespan=_lifespan,
    docs_url="/docs",
    openapi_url="/docs.json",
)

secure_headers = Secure.with_default_headers()
docs_secure_headers = Secure(
    csp=(
        ContentSecurityPolicy()
        .default_src("'self'")
        .script_src("'self'", "'unsafe-inline'", "cdn.jsdelivr.net")
        .style_src("'self'", "'unsafe-inline'", "cdn.jsdelivr.net")
        .img_src("'self'", "data:", "fastapi.tiangolo.com")
    )
)


@application.middleware("http")
async def add_security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    if request.url.path.startswith("/docs"):
        await docs_secure_headers.set_headers_async(response)
    else:
        await secure_headers.set_headers_async(response)
    return response


application.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
application.add_middleware(MetricsMiddleware)
application.mount("/metrics", make_asgi_app())  # type: ignore
application.include_router(router.routes)

from app.error_handlers import *  # noqa: E402, F403
