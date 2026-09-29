from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Ticket, Escalation, MemoryRecord
from ..dependencies import require_agent
from ..services.recurring_issues import recurring_issues
from ..services.hindsight_service import hindsight
from ..config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/dashboard")
def dashboard(_: User = Depends(require_agent), db: Session = Depends(get_db)):
    tickets = db.query(Ticket).all()
    customers = db.query(User).filter(User.role == "CUSTOMER").count()
    return {
        "customers": customers,
        "tickets": len(tickets),
        "open": sum(t.status in {"Open", "In Progress"} for t in tickets),
        "resolved": sum(t.status == "Resolved" for t in tickets),
        "escalated": sum(t.status == "Escalated" for t in tickets),
        "memories": db.query(MemoryRecord).count(),
        "escalations": db.query(Escalation).count(),
        "hindsight": hindsight.health(),
        "recurring_issues": recurring_issues(db)[:5],
    }

@router.get("/escalations")
def escalations(_: User = Depends(require_agent), db: Session = Depends(get_db)):
    rows = db.query(Escalation).order_by(Escalation.created_at.desc()).all()
    return [
        {
            "id": x.id, "ticket_id": x.ticket_id, "customer_id": x.customer_id,
            "reason": x.reason, "summary": x.summary, "status": x.status,
        } for x in rows
    ]

@router.get("/recurring-issues")
def recurring(_: User = Depends(require_agent), db: Session = Depends(get_db)):
    return recurring_issues(db)

@router.get("/settings")
def admin_settings(user: User = Depends(require_agent)):
    if user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
    return {
        "hindsight": hindsight.health(),
        "ai_configured": bool(settings.ai_api_url and settings.ai_api_key and settings.ai_model),
        "database": "connected",
        "version": "1.1.0",
    }
