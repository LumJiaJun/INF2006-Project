import time
import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(tags=["ops"])
logger = logging.getLogger("staysphere.health")

_start_time = time.time()


@router.get("/api/health")
def health(db: Session = Depends(get_db)):
    """
    Used for scalability/resilience: a load balancer or container
    orchestrator polls this to decide whether to route traffic to this
    instance, and whether to restart it. See docs/ARCHITECTURE.md and
    tests/04_scalability_resilience.
    """
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_ok = False
        logger.error("health_check_db_failure error=%s", exc)

    status = "healthy" if db_ok else "unhealthy"
    return {
        "status": status,
        "database": "up" if db_ok else "down",
        "uptime_seconds": round(time.time() - _start_time, 1),
    }
