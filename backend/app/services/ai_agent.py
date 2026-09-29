import httpx
from ..config import settings

def fallback_response(message: str, memories: list[str], similar_cases: list[dict]) -> tuple[str, list[str]]:
    lower = message.lower()
    reasons = []

    if memories:
        reasons.append("A relevant previous customer memory was recalled.")
        previous = memories[0]
        return (
            f"I found a relevant previous experience from your support history: {previous} "
            "I can use that context to avoid repeating unsuccessful troubleshooting. "
            "Would you like to try the previously successful approach first?",
            reasons + ["The recommendation is based on the customer's previous support history."]
        )

    if "crash" in lower or "crashing" in lower:
        reasons += ["The current message describes an application crash.", "No strong customer-specific memory was available."]
        return (
            "I can help troubleshoot the crash. Please tell me your operating system and the application version. "
            "If you have already tried a fix, tell me what happened so I do not repeat an unsuccessful step.",
            reasons
        )

    if "login" in lower or "password" in lower:
        reasons += ["The current message appears related to account access."]
        return (
            "Let's troubleshoot the login issue. Please confirm whether you can receive password-reset emails and whether the issue occurs on another device.",
            reasons
        )

    reasons += ["The response is based on the current support message."]
    return (
        "I understand the issue. I can help investigate it step by step. "
        "Please share the exact error message and what you have already tried.",
        reasons
    )

async def generate_response(message: str, memories: list[str], similar_cases: list[dict]) -> tuple[str, list[str]]:
    if not settings.ai_api_url or not settings.ai_api_key or not settings.ai_model:
        return fallback_response(message, memories, similar_cases)

    memory_text = "\n".join(f"- {m}" for m in memories) or "No relevant long-term memories found."
    cases_text = "\n".join(
        f"- {c['subject']} | {c['status']} | {c.get('solution','No recorded solution')}"
        for c in similar_cases
    ) or "No similar cases found."

    system = """You are a professional customer support agent.
Use recalled customer memory and similar cases when relevant.
Never claim you remember something unless it appears in the supplied memory.
Avoid repeating solutions marked failed.
If the issue is unresolved after multiple attempts, recommend human escalation.
Be concise, empathetic and practical."""

    prompt = f"""CUSTOMER MESSAGE:
{message}

RECALLED MEMORY:
{memory_text}

SIMILAR CASES:
{cases_text}

Respond to the customer and explain the next useful step."""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                settings.ai_api_url,
                headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                json={
                    "model": settings.ai_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
            )
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"]
            reasons = ["The response was grounded using the current message and recalled support context."]
            if memories:
                reasons.append("Relevant Hindsight memories were supplied to the model.")
            if similar_cases:
                reasons.append("Similar previous support cases were supplied.")
            return text, reasons
    except Exception:
        return fallback_response(message, memories, similar_cases)
