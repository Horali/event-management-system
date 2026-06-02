from dataclasses import dataclass
from decimal import Decimal
from typing import Dict


@dataclass(frozen=True)
class EventSalesReportDTO:
    event_id: str
    tickets_sold_per_category: Dict[str, int]  # category_name -> count
    bookings_count_by_status: Dict[str, int]   # status_name -> count
    total_revenue: Decimal


@dataclass(frozen=True)
class ParticipantDTO:
    customer_id: str
    customer_name: str
    ticket_category: str
    ticket_code: str
    check_in_status: str  # "Active", "CheckedIn", "Cancelled"
