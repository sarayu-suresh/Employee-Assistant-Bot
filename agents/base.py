from abc import ABC, abstractmethod

class Agent(ABC):
    @abstractmethod
    def can_handle(self, intent: str) -> bool:
        pass

    @abstractmethod
    def handle(self, message: str, user: str, session: dict) -> dict:
        """Returns dict to be used in JSONResponse"""
        pass
