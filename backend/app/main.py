from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routes import auth, customers, tickets, chat, admin, memory

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MemorySupport AI", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(tickets.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(memory.router)

@app.get("/")
def root():
    return {"name": "MemorySupport AI", "status": "running", "version": "1.1.0"}

@app.get("/health")
def health():
    from .services.hindsight_service import hindsight
    return {
        "status": "ok",
        "database": "connected",
        "hindsight": hindsight.health(),
    }
