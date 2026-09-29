from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Ticket, MemoryRecord, Escalation
from ..dependencies import current_user, require_agent
from ..services.hindsight_service import hindsight

router = APIRouter(prefix="/api", tags=["customers"])

@router.get("/customers")
def customers(_: User = Depends(require_agent), db: Session = Depends(get_db)):
    users = db.query(User).filter(User.role == "CUSTOMER").order_by(User.created_at.desc()).all()
    return [{"id": u.id, "name": u.name, "email": u.email} for u in users]

@router.get("/customers/{customer_id}")
def customer_detail(customer_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if user.role == "CUSTOMER" and user.id != customer_id:
        raise HTTPException(403, "Forbidden")
    customer = db.get(User, customer_id)
    if not customer or customer.role != "CUSTOMER":
        raise HTTPException(404, "Customer not found")
    tickets = db.query(Ticket).filter(Ticket.customer_id == customer_id).order_by(Ticket.created_at.desc()).all()
    memories = db.query(MemoryRecord).filter(MemoryRecord.customer_id == customer_id).order_by(MemoryRecord.created_at.desc()).all()
    escalations = db.query(Escalation).filter(Escalation.customer_id == customer_id).order_by(Escalation.created_at.desc()).all()
    return {
        "customer": {"id": customer.id, "name": customer.name, "email": customer.email},
        "tickets": tickets,
        "memories": memories,
        "hindsight": hindsight.list_memories(customer_id, 30),
        "hindsight_source": "Hindsight" if hindsight.connected else "Local Memory",
        "escalations": escalations,
    }
