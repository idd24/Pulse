from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower()

    if db.query(User).filter(User.email == email).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in an existing user",
    description="Verifies an email/password pair and returns a JWT access token and the user record. Use this to authenticate returning users after registration.",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower()
    user = db.query(User).filter(User.email == email).first()

    # Same 401 for unknown email and bad password to avoid user enumeration.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        user=UserResponse.model_validate(user),
    )
