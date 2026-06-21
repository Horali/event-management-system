# Event Management System

Backend REST API for an Event Ticketing & Booking System built with Clean Architecture and Domain-Driven Design (DDD).

---

## How to Run the Project

### 1. Clone the repository
```bash
git clone https://github.com/Horali/event-management-system
cd event-management-system
```

### 2. Install dependencies
```bash
uv sync
```

### 3. Configure environment variables
```bash
cp .env.example .env
```

### 4. Run the application
```bash
uv run uvicorn src.main:app --reload
```

Server runs at `http://127.0.0.1:8000`. Swagger UI available at `http://127.0.0.1:8000/docs`.

---

## How to Configure PostgreSQL

You can run PostgreSQL either via Docker or a local installation.

**Option A — Docker (recommended)**

Make sure Docker Desktop is running, then:
```bash
docker compose up -d
```
This starts a PostgreSQL 16 container on port **5433**. The default `.env` is already configured for this — no changes needed.

**Option B — Local PostgreSQL**

Create the database manually:
```sql
CREATE DATABASE event_management_db;
```
Then update `DATABASE_URL` in your `.env` to match your local credentials and port (typically `5432`):
```env
DATABASE_URL=postgresql+psycopg://<username>:<password>@localhost:5432/event_management_db
```

---

## How to Run Database Migration

```bash
uv run alembic upgrade head
```

This creates all 5 tables: `events`, `ticket_categories`, `bookings`, `tickets`, `refunds`.

---

## How to Run Tests

```bash
uv run pytest tests/unit/ -v
```

With coverage:
```bash
uv run pytest tests/unit/ --cov=src/domain --cov-report=term-missing
```

---

## Implemented User Stories

| UC | User Story | Layer |
|---|---|---|
| UC1 | Create Event | Domain ✅ |
| UC2 | Publish Event | Domain ✅ |
| UC3 | Cancel Event | Domain ✅ |
| UC4 | Create Ticket Category | Domain ✅ |
| UC5 | Disable Ticket Category | Domain ✅ |
| UC6 | View Available Events | Application ✅ |
| UC7 | View Event Details | Application ✅ |
| UC8 | Create Ticket Booking | Domain ✅ |
| UC9 | Calculate Booking Total Price | Domain ✅ |
| UC10 | Pay Booking | Domain ✅ |
| UC11 | Expire Booking | Domain ✅ |
| UC12 | View Purchased Tickets | Application ✅ |
| UC13 | Check In Ticket | Domain ✅ |
| UC14 | Reject Invalid Ticket Check-in | Domain ✅ |
| UC15 | Request Refund | Domain ✅ |
| UC16 | Approve Refund | Domain ✅ |
| UC17 | Reject Refund | Domain ✅ |
| UC18 | Mark Refund as Paid Out | Domain ✅ |
| UC19 | View Event Sales Report | Application ✅ |
| UC20 | View Event Participants | Application ✅ |

---

## Implemented Domain Events

| Domain Event | Raised When |
|---|---|
| `EventCreated` | A new event is successfully created |
| `EventPublished` | An event transitions from Draft to Published |
| `EventCancelled` | An event is cancelled |
| `TicketCategoryCreated` | A ticket category is added to an event |
| `TicketCategoryDisabled` | A ticket category is disabled |
| `TicketReserved` | A booking is created |
| `BookingPaid` | A booking payment is completed |
| `BookingExpired` | A booking passes its payment deadline unpaid |
| `TicketCheckedIn` | A ticket is checked in at the event venue |
| `RefundRequested` | A customer requests a refund |
| `RefundApproved` | An organizer approves a refund request |
| `RefundRejected` | An organizer rejects a refund request |
| `RefundPaidOut` | A refund is marked as paid out |

---

## Implemented Application Service Interfaces

| Interface | Location | Purpose |
|---|---|---|
| `IPaymentGateway` | `src/application/interfaces/payment_gateway.py` | Process booking payments via external payment gateway |
| `IRefundPaymentService` | `src/application/interfaces/refund_service.py` | Process refund payouts via bank/external service |
| `INotificationService` | `src/application/interfaces/notification_service.py` | Send email/WhatsApp notifications to customers |
| `IDomainEventDispatcher` | `src/application/interfaces/domain_event_dispatcher.py` | Dispatch domain events to application-level handlers |

Concrete implementations are in `src/infrastructure/services/`.
