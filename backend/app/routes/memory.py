from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, MemoryRecord, Ticket, Escalation
from ..dependencies import current_user
from ..services.hindsight_service import hindsight

router = APIRouter(prefix="/api/memory", tags=["memory"])

def can_access(user, customer_id):
    return user.role in {"SUPPORT_AGENT", "ADMIN"} or user.id == customer_id

@router.get("/status")
def memory_status(_: User = Depends(current_user)):
    return hindsight.health()

@router.get("/customer/{customer_id}")
def memory_customer(customer_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not can_access(user, customer_id):
        raise HTTPException(403, "Forbidden")
    local = db.query(MemoryRecord).filter(
        MemoryRecord.customer_id == customer_id
    ).order_by(MemoryRecord.created_at.desc()).limit(50).all()
    hindsight_items = hindsight.list_memories(customer_id, limit=50)
    return {
        "source": "Hindsight" if hindsight.connected else "Local Memory",
        "hindsight_memories": hindsight_items,
        "local_memories": [
            {"id": m.id, "ticket_id": m.ticket_id, "content": m.content,
             "kind": m.kind, "created_at": m.created_at.isoformat()}
            for m in local
        ],
    }

@router.get("/customer/{customer_id}/summary")
def memory_summary(customer_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not can_access(user, customer_id):
        raise HTTPException(403, "Forbidden")
    memories = db.query(MemoryRecord).filter(MemoryRecord.customer_id == customer_id).all()
    tickets = db.query(Ticket).filter(Ticket.customer_id == customer_id).all()
    escalations = db.query(Escalation).filter(Escalation.customer_id == customer_id).all()
    return {
        "total_memories": len(memories),
        "successful_solutions": sum(m.kind == "solution_outcome" and "worked" in m.content.lower() for m in memories),
        "failed_solutions": sum(m.kind == "solution_outcome" and "didn't work" in m.content.lower() for m in memories),
        "tickets": len(tickets),
        "resolved_tickets": sum(t.status == "Resolved" for t in tickets),
        "escalations": len(escalations),
        "recent_learning": [
            {"kind": m.kind, "content": m.content, "created_at": m.created_at.isoformat()}
            for m in sorted(memories, key=lambda x: x.created_at, reverse=True)[:8]
        ],
    }
