import uuid
from agents.base import Agent
from scripts.cards import build_leave_confirmation_card

class LeaveRequestAgent(Agent):
    def can_handle(self, intent: str) -> bool:
        return intent == "raise_leave_request"

    def handle(self, message: str, user: str, session: dict) -> dict:
        request_id = str(uuid.uuid4())
        session.update({
            "state": "awaiting_confirmation",
            "reason": message,
            "ticket_type": "Leave",
            "request_id": request_id
        })

        return {
            "session": session,
            "response": build_leave_confirmation_card("Do you want to submit this leave request?", message)
        }