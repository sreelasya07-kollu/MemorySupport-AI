from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import RegisterIn, LoginIn, TokenOut, UserOut
from ..auth import hash_password, verify_password, create_token
from ..dependencies import current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(name=data.name, email=data.email.lower(), password_hash=hash_password(data.password), role="CUSTOMER")
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_token(user.id, user.role), "token_type": "bearer", "user": user}

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_token(user.id, user.role), "token_type": "bearer", "user": user}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user
