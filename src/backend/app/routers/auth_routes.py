import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger("staysphere.auth")


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = models.User(
        name=payload.name,
        email=payload.email,
        password_hash=auth.hash_password(payload.password),
        role=models.UserRole.guest,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("user_registered user_id=%s", user.user_id)
    return user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.password_hash):
        # Deliberately generic message: does not reveal whether the
        # email exists (mitigates user enumeration).
        logger.warning("login_failed email=%s", payload.email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = auth.create_access_token({"sub": str(user.user_id), "role": user.role})
    logger.info("login_success user_id=%s", user.user_id)
    return schemas.Token(access_token=token, user=user)


@router.post("/logout")
def logout():
    # JWTs are stateless; logout is handled client-side by discarding
    # the token. Documented here for completeness of the auth workflow.
    return {"message": "Logged out. Discard the access token client-side."}
