from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.config import settings
from app.database import Base, engine
from app.rate_limit import limiter
from app.routers import metros, query

app = FastAPI(title="Athena Shell API", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(metros.router)
app.include_router(query.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Behind nginx, request.client.host is otherwise always 127.0.0.1, which
# would make the rate limiter treat every visitor as the same client. Wrapped
# separately (not reassigning `app`) so tests and other imports still get the
# plain FastAPI instance; gunicorn/uvicorn should point at this instead.
asgi_app = ProxyHeadersMiddleware(app, trusted_hosts="127.0.0.1")
