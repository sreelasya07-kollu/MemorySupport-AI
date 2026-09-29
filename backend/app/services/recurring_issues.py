import re
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
from ..models import Ticket

STOP = {
    "the","and","for","with","after","when","from","this","that","have","has",
    "issue","problem","please","my","your","application","app","customer"
}

def normalize(text: str):
    words = re.findall(r"[a-zA-Z]{4,}", (text or "").lower())
    return [w for w in words if w not in STOP]

def recurring_issues(db: Session):
    tickets = db.query(Ticket).all()
    groups = defaultdict(list)
    for t in tickets:
        tokens = normalize(f"{t.subject} {t.description}")
        if not tokens:
            continue
        # Prefer category as the stable business grouping.
        key = (t.category or "Other").strip()
        groups[key].append(t)

    result = []
    for category, rows in groups.items():
        if len(rows) < 2:
            continue
        customers = sorted({t.customer_id for t in rows})
        open_count = sum(t.status in {"Open","In Progress","Escalated"} for t in rows)
        resolved = sum(t.status == "Resolved" for t in rows)
        severity = "High" if any(t.priority == "High" for t in rows) else ("Medium" if any(t.priority == "Medium" for t in rows) else "Low")
        examples = [{"id": t.id, "subject": t.subject, "status": t.status} for t in rows[:5]]
        result.append({
            "issue": category,
            "count": len(rows),
            "affected_customers": len(customers),
            "open_tickets": open_count,
            "resolved_tickets": resolved,
            "severity": severity,
            "examples": examples,
        })
    result.sort(key=lambda x: (-x["count"], x["issue"]))
    return result
