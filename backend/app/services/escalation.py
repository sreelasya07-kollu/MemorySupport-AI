from sqlalchemy.orm import Session
from ..models import Ticket, Message, Escalation, User, MemoryRecord
from .hindsight_service import hindsight

def build_summary(db: Session, ticket: Ticket, customer: User):
    messages = db.query(Message).filter(Message.ticket_id == ticket.id).order_by(Message.created_at).all()
    outcomes = db.query(MemoryRecord).filter(
        MemoryRecord.ticket_id == ticket.id,
        MemoryRecord.kind == "solution_outcome"
    ).order_by(MemoryRecord.created_at).all()
    lines = [
        f"Customer: {customer.name}",
        f"Email: {customer.email}",
        f"Ticket: TKT-{ticket.id:05d}",
        f"Issue: {ticket.subject}",
        f"Category: {ticket.category}",
        f"Priority: {ticket.priority}",
        f"Status: {ticket.status}",
        "",
        "Previous solution outcomes:",
    ]
    lines += [f"- {x.content}" for x in outcomes[-8:]] or ["- No feedback recorded."]
    lines.append("")
    lines.append("Conversation:")
    for m in messages[-12:]:
        lines.append(f"{m.sender_role}: {m.content}")
    return "\n".join(lines)

def create_escalation(db: Session, ticket: Ticket, customer: User, reason: str):
    existing = db.query(Escalation).filter(
        Escalation.ticket_id == ticket.id,
        Escalation.status == "Open"
    ).first()
    if existing:
        return existing

    summary = build_summary(db, ticket, customer)
    ticket.status = "Escalated"
    esc = Escalation(
        ticket_id=ticket.id,
        customer_id=customer.id,
        reason=reason,
        summary=summary,
    )
    db.add(esc)
    db.commit()
    db.refresh(esc)
    hindsight.retain(
        customer.id,
        f"Ticket TKT-{ticket.id:05d} was escalated to a human. Reason: {reason}. Summary: {summary}",
        context="support escalation",
        document_id=f"escalation_{esc.id}",
    )
    return esc
