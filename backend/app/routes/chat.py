from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Ticket, Message, MemoryRecord
from ..schemas import ChatIn, ChatOut
from ..dependencies import current_user
from ..services.hindsight_service import hindsight
from ..services.ai_agent import generate_response

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("", response_model=ChatOut)
async def chat(data: ChatIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    ticket = db.get(Ticket, data.ticket_id) if data.ticket_id else None
    if ticket and ticket.customer_id != user.id and user.role == "CUSTOMER":
        raise HTTPException(403, "Forbidden")
    if not ticket:
        ticket = Ticket(
            customer_id=user.id,
            subject=data.message[:80],
            description=data.message,
            category="Technical Issue",
            priority="Medium",
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

    db.add(Message(ticket_id=ticket.id, sender_role="CUSTOMER", content=data.message))
    db.commit()

    memories = hindsight.recall(user.id, data.message, limit=5)
    local = db.query(MemoryRecord).filter(
        MemoryRecord.customer_id == user.id
    ).order_by(MemoryRecord.created_at.desc()).limit(12).all()
    local_texts = [m.content for m in local]

    combined = []
    for m in memories + local_texts:
        if m not in combined:
            combined.append(m)

    similar = []
    for t in db.query(Ticket).filter(
        Ticket.customer_id == user.id, Ticket.id != ticket.id
    ).order_by(Ticket.created_at.desc()).limit(8).all():
        outcome = next(
            (m.content for m in db.query(MemoryRecord).filter(
                MemoryRecord.ticket_id == t.id,
                MemoryRecord.kind == "solution_outcome"
            ).order_by(MemoryRecord.created_at.desc()).all()),
            "No recorded solution"
        )
        similar.append({
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "solution": outcome,
        })

    failed_attempts = db.query(MemoryRecord).filter(
        MemoryRecord.ticket_id == ticket.id,
        MemoryRecord.kind == "solution_outcome"
    ).count()

    response, reasons = await generate_response(data.message, combined[:5], similar[:3])
    if memories:
        reasons.insert(0, "Relevant Hindsight memory was recalled for this customer.")
    elif local_texts:
        reasons.insert(0, "Local customer memory was used because no strong Hindsight result was returned.")
    if failed_attempts >= 2:
        reasons.append("Multiple unsuccessful attempts have been recorded; human escalation is suggested.")

    db.add(Message(ticket_id=ticket.id, sender_role="AI_AGENT", content=response))
    db.commit()

    hindsight.retain(
        user.id,
        f"Support conversation for TKT-{ticket.id:05d}. Customer: {data.message} Agent: {response}",
        context="customer support conversation",
        document_id=f"conversation_{ticket.id}_{db.query(Message).filter(Message.ticket_id == ticket.id).count()}",
    )

    return {
        "ticket_id": ticket.id,
        "response": response,
        "memories": memories[:5] if memories else local_texts[:5],
        "similar_cases": similar[:3],
        "recommendation_reasons": reasons,
        "memory_source": "Hindsight" if memories else ("Local Memory" if local_texts else "None"),
        "failed_attempts": failed_attempts,
        "escalation_suggested": failed_attempts >= 2,
    }
