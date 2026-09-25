import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import auth_routes, listings, bookings, ml, health, admin, recommendations, reviews, chatbot

# --- Logging / monitoring ---------------------------------------------------
# Structured-ish logging to stdout. In AWS deployment this is picked up by
# CloudWatch Logs automatically when running on ECS/EC2 with the CloudWatch
# agent or awslogs driver — see docs/DEPLOYMENT.md.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
)
logger = logging.getLogger("staysphere")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="StaySphere API",
    description="Academic simulation of an Airbnb-style booking platform for INF2006.",
    version="0.1.0",
)

# CORS: restricted to explicit origins from env, not "*", so any deployed
# frontend origin must be allow-listed deliberately (least privilege).
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:8080,http://127.0.0.1:8080",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 1)
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%s",
        request.method, request.url.path, response.status_code, duration_ms,
    )
    return response


app.include_router(health.router)
app.include_router(auth_routes.router)
app.include_router(listings.router)
app.include_router(bookings.router)
app.include_router(ml.router)
app.include_router(admin.router)
app.include_router(recommendations.router)
app.include_router(reviews.router)
app.include_router(chatbot.router)


@app.get("/")
def root():
    return {"service": "StaySphere API", "docs": "/docs", "health": "/api/health"}
