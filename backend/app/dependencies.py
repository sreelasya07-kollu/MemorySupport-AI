from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .auth import decode_token
from .models import User

security = HTTPBearer()

def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    payload = decode_token(credentials.credentials)
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_agent(user: User = Depends(current_user)):
    if user.role not in {"SUPPORT_AGENT", "ADMIN"}:
        raise HTTPException(status_code=403, detail="Support-agent access required")
    return user
