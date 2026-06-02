from abc import ABC, abstractmethod
from typing import List
from src.domain.events.base import BaseDomainEvent


class IDomainEventDispatcher(ABC):
    """Interface for dispatching domain events to their respective application-level handlers."""

    @abstractmethod
    def dispatch(self, event: BaseDomainEvent) -> None:
        """Dispatch a single domain event."""
        pass

    @abstractmethod
    def dispatch_all(self, events: List[BaseDomainEvent]) -> None:
        """Dispatch multiple domain events in sequence."""
        pass
