from hindsight_client import Hindsight
from ..config import settings

class HindsightService:
    def __init__(self):
        self.enabled = bool(settings.hindsight_api_url)
        self.client = None
        self.last_error = None
        if self.enabled:
            kwargs = {"base_url": settings.hindsight_api_url}
            if settings.hindsight_api_key:
                kwargs["api_key"] = settings.hindsight_api_key
            try:
                self.client = Hindsight(**kwargs)
            except Exception as exc:
                self.client = None
                self.last_error = str(exc)

    @property
    def connected(self):
        return self.client is not None

    def bank_id(self, customer_id: int) -> str:
        return f"customer_{customer_id}"

    def ensure_bank(self, customer_id: int):
        if not self.client:
            return False
        try:
            self.client.create_bank(
                bank_id=self.bank_id(customer_id),
                name=f"Customer {customer_id} Support Memory",
                mission=(
                    "Remember this customer's support history, previous issues, "
                    "successful and failed solutions, preferences, recurring problems "
                    "and escalation context. Use memory to personalize future support."
                ),
            )
        except Exception:
            pass
        return True

    def retain(self, customer_id: int, content: str, context="customer support", document_id=None):
        if not self.client:
            return False
        try:
            self.ensure_bank(customer_id)
            kwargs = {
                "bank_id": self.bank_id(customer_id),
                "content": content,
                "context": context,
            }
            if document_id:
                kwargs["document_id"] = document_id
            self.client.retain(**kwargs)
            return True
        except Exception as exc:
            self.last_error = str(exc)
            return False

    def recall(self, customer_id: int, query: str, limit=5):
        if not self.client:
            return []
        try:
            self.ensure_bank(customer_id)
            result = self.client.recall(
                bank_id=self.bank_id(customer_id),
                query=query,
                max_tokens=2500,
                budget="mid",
            )
            return [r.text for r in result.results[:limit]]
        except Exception as exc:
            self.last_error = str(exc)
            return []

    def list_memories(self, customer_id: int, limit=50):
        if not self.client:
            return []
        try:
            self.ensure_bank(customer_id)
            result = self.client.list_memories(
                bank_id=self.bank_id(customer_id),
                limit=limit,
            )
            items = []
            for r in result:
                text = getattr(r, "text", None) or getattr(r, "content", None) or str(r)
                items.append(text)
            return items
        except Exception as exc:
            self.last_error = str(exc)
            return []

    def health(self):
        if not self.client:
            return {"enabled": False, "provider": "Local Memory", "mode": "fallback",
                    "message": "Hindsight is not configured or could not initialize."}
        return {"enabled": True, "provider": "Hindsight", "mode": "configured",
                "message": "Hindsight client is configured."}

hindsight = HindsightService()
