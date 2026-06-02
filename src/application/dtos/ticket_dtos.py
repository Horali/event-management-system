from dataclasses import dataclass
from src.domain.entities.ticket import Ticket


@dataclass(frozen=True)
class TicketDTO:
    code: str
    status: str

    @classmethod
    def from_domain(cls, ticket: Ticket) -> "TicketDTO":
        return cls(
            code=ticket.code.value,
            status=ticket.status.name,
        )
