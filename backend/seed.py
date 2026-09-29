from app.database import Base, engine, SessionLocal
from app.models import User, Ticket, Message, MemoryRecord
from app.auth import hash_password
from app.services.hindsight_service import hindsight

Base.metadata.create_all(bind=engine)
db = SessionLocal()

def get_user(email, name, password, role):
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(name=name, email=email, password_hash=hash_password(password), role=role)
        db.add(u); db.commit(); db.refresh(u)
    return u

sarah = get_user("sarah@example.com", "Sarah Johnson", "Sarah123!", "CUSTOMER")
alex = get_user("alex@example.com", "Alex Kim", "Alex123!", "SUPPORT_AGENT")

# Optional admin for demonstrating role separation.
admin = get_user("admin@example.com", "Admin User", "Admin123!", "ADMIN")

def add_demo_ticket(customer, subject, description, category, priority, status, solution=None, worked=False):
    exists = db.query(Ticket).filter(Ticket.customer_id == customer.id, Ticket.subject == subject).first()
    if exists:
        return exists
    t = Ticket(customer_id=customer.id, subject=subject, description=description,
               category=category, priority=priority, status=status)
    db.add(t); db.commit(); db.refresh(t)
    db.add(Message(ticket_id=t.id, sender_role="CUSTOMER", content=description))
    if solution:
        db.add(Message(ticket_id=t.id, sender_role="AI_AGENT", content=solution))
        db.add(MemoryRecord(
            customer_id=customer.id, ticket_id=t.id,
            content=f"Ticket TKT-{t.id:05d}: Solution attempted: {solution}. Customer outcome: {'Worked' if worked else 'Did not Work'}.",
            kind="solution_outcome"
        ))
    db.add(MemoryRecord(
        customer_id=customer.id, ticket_id=t.id,
        content=f"{subject}: {description}",
        kind="ticket"
    ))
    db.commit()
    hindsight.retain(
        customer.id,
        f"{subject}. {description}. Previous solution: {solution or 'None'}. Outcome: {'Worked' if worked else 'Not recorded'}.",
        context="demo support history",
        document_id=f"demo_ticket_{t.id}",
    )
    return t

add_demo_ticket(
    sarah,
    "Application crash after update",
    "CloudDesk crashes when I upload a PDF after the latest update.",
    "Application Error", "High", "Resolved",
    "Clear the application cache and restart CloudDesk.", True
)
add_demo_ticket(
    sarah,
    "PDF upload crashes again",
    "The same PDF upload crash happened again after another update.",
    "Application Error", "High", "In Progress",
    "Reinstall the application.", False
)
add_demo_ticket(
    alex,
    "Login problem",
    "Customer cannot log in after changing their password.",
    "Account Access", "Medium", "Open",
    None, False
)
# A second customer gives the recurring-issues dashboard meaningful data.
mira = get_user("mira@example.com", "Mira Patel", "Mira123!", "CUSTOMER")
add_demo_ticket(mira, "PDF upload crash", "PDF upload crashes on the latest release.", "Application Error", "High", "Open")
add_demo_ticket(mira, "Login failure", "Login fails after a password reset.", "Account Access", "Medium", "Open")

print("Seed complete.")
print("Customer: sarah@example.com / Sarah123!")
print("Support:  alex@example.com / Alex123!")
print("Admin:    admin@example.com / Admin123!")
db.close()
