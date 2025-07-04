# app/routers/auth.py - Make sure it exports router properly
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, User as UserSchema, Token
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
)
from app.utils import generate_id
from app.config import settings

# IMPORTANT: Make sure this router variable exists and is exported
router = APIRouter(prefix="/auth", tags=["authentication"])

print("✅ Auth router created")


@router.post("/register", response_model=UserSchema)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        id=generate_id(),
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        bio=user.bio,
        phone=user.phone,
        address=user.address,
        profile_image=user.profile_image,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    print(f"✅ User registered: {db_user.email}")
    return db_user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # OAuth2PasswordRequestForm uses 'username' field, but we'll treat it as email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    print(f"✅ User logged in: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    print(f"✅ /auth/me called for user: {current_user.email}")
    return current_user


# IMPORTANT: Make sure this line is at the end of the file
print(
    f"✅ Auth router configured with routes: {[route.path for route in router.routes]}"
)
