# MemorySupport AI

A full-stack, Hindsight-powered customer support platform.

## Features
- Customer registration/login with JWT
- Support-agent login
- Customer-specific tickets and conversations
- Hindsight long-term memory
- Memory recalled in support chat
- Successful/failed solution feedback
- Similar previous cases
- Customer memory timeline
- Human escalation with AI-style case summary
- Support dashboard
- Demo accounts

## Requirements
- Python 3.11+
- Node.js 18+
- Optional: Hindsight server/cloud credentials
- Optional: OpenAI-compatible API key for richer AI responses

## 1. Backend

```bash
cd backend
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
python seed.py
uvicorn app.main:app --reload --port 8000
```

Backend: http://localhost:8000
API docs: http://localhost:8000/docs

## 2. Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Demo accounts

Customer:
- Email: sarah@example.com
- Password: Sarah123!

Support agent:
- Email: alex@example.com
- Password: Alex123!

## Hindsight

The backend supports Hindsight through `hindsight-client`.

For local Hindsight:
HINDSIGHT_API_URL=http://localhost:8888

For Hindsight Cloud:
HINDSIGHT_API_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=your_key

Each customer gets a customer-scoped memory bank:
`customer_<customer_id>`

If Hindsight is not configured, the app still runs using its local memory records so the UI can be tested. Configure Hindsight for the actual hackathon memory demonstration.

## AI

Set:
- AI_API_URL
- AI_API_KEY
- AI_MODEL

The app uses an OpenAI-compatible chat endpoint when configured. Without an AI key, it uses a deterministic support fallback so the application remains runnable.

## Demo flow

1. Login as Sarah.
2. Open Support Chat.
3. Ask: `My application keeps crashing after the latest update.`
4. The seeded customer history contains a previous successful cache-reset solution.
5. The agent recalls that memory.
6. Click `Worked` or `Didn't Work`.
7. Login as Alex.
8. Open Sarah's profile and inspect the memory/ticket history.
9. Use the dashboard to view escalations and recurring issues.

## Security notes
This is a hackathon prototype. Use HTTPS, a production database, secure secret storage, refresh-token rotation and stronger operational controls before production use.
