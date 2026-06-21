from fastapi import Depends
from sqlalchemy.orm import Session
from src.db import get_session

from src.infrastructure.repositories import EventRepository, BookingRepository, RefundRepository
from src.infrastructure.services import (
    DomainEventDispatcher,
    MockPaymentGateway,
    MockRefundPaymentService,
    MockNotificationService,
)

# Handlers imports
from src.application.commands.event_commands import (
    CreateEventHandler,
    PublishEventHandler,
    CancelEventHandler,
)
from src.application.commands.ticket_category_commands import (
    CreateTicketCategoryHandler,
    DisableTicketCategoryHandler,
)
from src.application.commands.ticket_commands import CheckInTicketHandler
from src.application.commands.booking_commands import (
    CreateBookingHandler,
    PayBookingHandler,
    ExpireBookingHandler,
)
from src.application.commands.refund_commands import (
    RequestRefundHandler,
    ApproveRefundHandler,
    RejectRefundHandler,
    MarkRefundPaidOutHandler,
)
from src.application.queries.report_queries import (
    GetSalesReportHandler,
    GetEventParticipantsHandler,
)

def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()

# Repositories
def get_event_repository(db: Session = Depends(get_db)) -> EventRepository:
    return EventRepository(db)

def get_booking_repository(db: Session = Depends(get_db)) -> BookingRepository:
    return BookingRepository(db)

def get_refund_repository(db: Session = Depends(get_db)) -> RefundRepository:
    return RefundRepository(db)

# Services
def get_domain_event_dispatcher() -> DomainEventDispatcher:
    return DomainEventDispatcher()

def get_payment_gateway() -> MockPaymentGateway:
    return MockPaymentGateway()

def get_refund_payment_service() -> MockRefundPaymentService:
    return MockRefundPaymentService()

def get_notification_service() -> MockNotificationService:
    return MockNotificationService()

# Command Handlers
def get_create_event_handler(
    event_repo: EventRepository = Depends(get_event_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> CreateEventHandler:
    return CreateEventHandler(event_repo, dispatcher)

def get_publish_event_handler(
    event_repo: EventRepository = Depends(get_event_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> PublishEventHandler:
    return PublishEventHandler(event_repo, dispatcher)

def get_cancel_event_handler(
    event_repo: EventRepository = Depends(get_event_repository),
    booking_repo: BookingRepository = Depends(get_booking_repository),
    refund_repo: RefundRepository = Depends(get_refund_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> CancelEventHandler:
    return CancelEventHandler(event_repo, booking_repo, refund_repo, dispatcher)

def get_create_ticket_category_handler(
    event_repo: EventRepository = Depends(get_event_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> CreateTicketCategoryHandler:
    return CreateTicketCategoryHandler(event_repo, dispatcher)

def get_disable_ticket_category_handler(
    event_repo: EventRepository = Depends(get_event_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> DisableTicketCategoryHandler:
    return DisableTicketCategoryHandler(event_repo, dispatcher)

def get_check_in_ticket_handler(
    booking_repo: BookingRepository = Depends(get_booking_repository),
    event_repo: EventRepository = Depends(get_event_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> CheckInTicketHandler:
    return CheckInTicketHandler(booking_repo, event_repo, dispatcher)

def get_create_booking_handler(
    event_repo: EventRepository = Depends(get_event_repository),
    booking_repo: BookingRepository = Depends(get_booking_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> CreateBookingHandler:
    return CreateBookingHandler(event_repo, booking_repo, dispatcher)

def get_pay_booking_handler(
    booking_repo: BookingRepository = Depends(get_booking_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> PayBookingHandler:
    return PayBookingHandler(booking_repo, dispatcher)

def get_expire_booking_handler(
    booking_repo: BookingRepository = Depends(get_booking_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> ExpireBookingHandler:
    return ExpireBookingHandler(booking_repo, dispatcher)

def get_request_refund_handler(
    booking_repo: BookingRepository = Depends(get_booking_repository),
    event_repo: EventRepository = Depends(get_event_repository),
    refund_repo: RefundRepository = Depends(get_refund_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> RequestRefundHandler:
    return RequestRefundHandler(booking_repo, event_repo, refund_repo, dispatcher)

def get_approve_refund_handler(
    refund_repo: RefundRepository = Depends(get_refund_repository),
    booking_repo: BookingRepository = Depends(get_booking_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> ApproveRefundHandler:
    return ApproveRefundHandler(refund_repo, booking_repo, dispatcher)

def get_reject_refund_handler(
    refund_repo: RefundRepository = Depends(get_refund_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> RejectRefundHandler:
    return RejectRefundHandler(refund_repo, dispatcher)

def get_mark_refund_paid_out_handler(
    refund_repo: RefundRepository = Depends(get_refund_repository),
    dispatcher: DomainEventDispatcher = Depends(get_domain_event_dispatcher),
) -> MarkRefundPaidOutHandler:
    return MarkRefundPaidOutHandler(refund_repo, dispatcher)

# Query Handlers
def get_sales_report_handler(
    event_repo: EventRepository = Depends(get_event_repository),
    booking_repo: BookingRepository = Depends(get_booking_repository),
) -> GetSalesReportHandler:
    return GetSalesReportHandler(event_repo, booking_repo)

def get_event_participants_handler(
    event_repo: EventRepository = Depends(get_event_repository),
    booking_repo: BookingRepository = Depends(get_booking_repository),
) -> GetEventParticipantsHandler:
    return GetEventParticipantsHandler(event_repo, booking_repo)