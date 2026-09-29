from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Ticket, Message, MemoryRecord
from ..schemas import TicketCreate, TicketOut, FeedbackIn, EscalateIn
from ..dependencies import current_user, require_agent
from ..services.hindsight_service import hindsight
from ..services.escalation import create_escalation

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

def allowed_ticket(ticket, user):
    return user.role in {"SUPPORT_AGENT", "ADMIN"} or ticket.customer_id == user.id

@router.post("", response_model=TicketOut)
def create_ticket(data: TicketCreate, user: User = Depends(current_user), db: Session = Depends(get_db)):
    ticket = Ticket(customer_id=user.id, **data.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    db.add(Message(ticket_id=ticket.id, sender_role="CUSTOMER", content=data.description))
    db.add(MemoryRecord(
        customer_id=user.id, ticket_id=ticket.id,
        content=f"Ticket TKT-{ticket.id:05d}: {data.subject} — {data.description}",
        kind="ticket"
    ))
    db.commit()
    hindsight.retain(
        user.id,
        f"Customer {user.name} opened TKT-{ticket.id:05d}. Subject: {data.subject}. Issue: {data.description}",
        context="support ticket opened",
        document_id=f"ticket_{ticket.id}",
    )
    return ticket

@router.get("", response_model=list[TicketOut])
def list_tickets(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = db.query(Ticket)
    if user.role == "CUSTOMER":
        q = q.filter(Ticket.customer_id == user.id)
    return q.order_by(Ticket.updated_at.desc()).all()

@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket or not allowed_ticket(ticket, user):
        raise HTTPException(404, "Ticket not found")
    return ticket

@router.post("/feedback")
def feedback(data: FeedbackIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    ticket = db.get(Ticket, data.ticket_id)
    if not ticket or not allowed_ticket(ticket, user):
        raise HTTPException(404, "Ticket not found")
    content = f"Ticket TKT-{ticket.id:05d}: Solution attempted: {data.solution}. Customer outcome: {data.outcome}."
    db.add(MemoryRecord(
        customer_id=ticket.customer_id,
        ticket_id=ticket.id,
        content=content,
        kind="solution_outcome"
    ))
    if data.outcome.lower() == "worked":
        ticket.status = "Resolved"
    else:
        ticket.status = "In Progress"
    ticket.updated_at = datetime.utcnow()
    db.commit()
    hindsight.retain(
        ticket.customer_id,
        content,
        context="successful solution" if data.outcome.lower() == "worked" else "failed support solution",
        document_id=f"feedback_{ticket.id}_{datetime.utcnow().timestamp()}",
    )
    return {"ok": True, "status": ticket.status}

@router.post("/escalate")
def escalate(data: EscalateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    ticket = db.get(Ticket, data.ticket_id)
    if not ticket or not allowed_ticket(ticket, user):
        raise HTTPException(404, "Ticket not found")
    customer = db.get(User, ticket.customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    esc = create_escalation(db, ticket, customer, data.reason)
    return {
        "id": esc.id,
        "ticket_id": esc.ticket_id,
        "status": esc.status,
        "reason": esc.reason,
        "summary": esc.summary,
    }
