from typing import List
from src.application.interfaces.domain_event_dispatcher import IDomainEventDispatcher
from src.domain.events.base import BaseDomainEvent

class DomainEventDispatcher(IDomainEventDispatcher):
    """Concrete implementation of IDomainEventDispatcher that logs events to stdout."""

    def dispatch(self, event: BaseDomainEvent) -> None:
        print(f"[Domain Event] Dispatched: {event.__class__.__name__} - {event}")

    def dispatch_all(self, events: List[BaseDomainEvent]) -> None:
        for event in events:
            self.dispatch(event)