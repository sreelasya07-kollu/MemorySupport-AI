from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    model_config = ConfigDict(from_attributes=True)

class TokenOut(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class TicketCreate(BaseModel):
    subject: str
    description: str
    category: str = "Technical Issue"
    priority: str = "Medium"

class TicketOut(BaseModel):
    id: int
    customer_id: int
    subject: str
    description: str
    category: str
    priority: str
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatIn(BaseModel):
    message: str
    ticket_id: int | None = None

class FeedbackIn(BaseModel):
    ticket_id: int
    outcome: str
    solution: str

class EscalateIn(BaseModel):
    ticket_id: int
    reason: str = "Multiple unsuccessful troubleshooting attempts."

class ChatOut(BaseModel):
    ticket_id: int
    response: str
    memories: list[str]
    similar_cases: list[dict]
    recommendation_reasons: list[str]
    memory_source: str = "Local Memory"
    failed_attempts: int = 0
    escalation_suggested: bool = False
