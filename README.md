# Event Management System

## Project Overview
The Event Management System is a backend REST API developed to facilitate event ticketing and booking. This project implements Clean Architecture and Domain-Driven Design (DDD) principles to ensure clear separation between domain logic, application use cases, infrastructure, and presentation layers.

It allows Event Organizers to create and manage events, Customers to book and pay for tickets, and Gate Officers to validate tickets during check-in.

## Prerequisites
Before you begin, ensure you have the following installed:
- **Python 3.14+**
- **uv** (for fast dependency management)
- **Docker Desktop** (for running PostgreSQL)

## Setup Guide

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
The default `.env` is already configured to connect to the Docker PostgreSQL instance. No changes needed unless you're using a different setup.

### 4. Start the PostgreSQL database with Docker
Make sure Docker Desktop is running, then:
```bash
docker compose up -d
```
This starts a PostgreSQL 16 container on port **5433**.

To verify it's running:
```bash
docker compose ps
```

To stop it when you're done:
```bash
docker compose down
```

### 5. Run database migrations
```bash
uv run alembic upgrade head
```
This creates all the required tables in the database.

### 6. Run the application
```bash
uv run uvicorn src.main:app --reload
```
The server starts at `http://127.0.0.1:8000`. API documentation (Swagger UI) is available at `http://127.0.0.1:8000/docs`.

---

## Running Tests

Domain layer unit tests are pure Python — no database or server required.

```bash
uv run pytest tests/unit/ -v
```

With coverage:
```bash
uv run pytest tests/unit/ --cov=src/domain --cov-report=term-missing
```

---

## Architecture

This project follows Clean Architecture with four layers:

```
Presentation Layer   — FastAPI routes (Week 13)
Application Layer    — Use cases, commands, queries (Week 11)
Infrastructure Layer — SQLAlchemy, PostgreSQL, repositories (Week 12)
Domain Layer         — Business logic, pure Python, no dependencies (Week 9-10)
```

### Domain Layer (`src/domain/`)
The innermost ring. Zero dependencies on any framework or database.

- `value_objects/` — `Money`, `DateTimeRange`, `EventStatus`, `BookingStatus`, and more
- `entities/` — `TicketCategory`, `Ticket`
- `aggregates/` — `Event`, `Booking`, `Refund` (aggregate roots)
- `events/` — 14 domain event dataclasses
- `repositories/` — `IEventRepository`, `IBookingRepository`, `IRefundRepository` (abstract interfaces)

### Infrastructure Layer (`src/infrastructure/`)

- `models/` — SQLAlchemy ORM models mapping domain aggregates to PostgreSQL tables
- `repositories/` — Concrete implementations of the repository interfaces

### Database Schema
5 tables managed by Alembic migrations:
- `events` + `ticket_categories`
- `bookings` + `tickets`
- `refunds`

---

## Domain Events

| Domain Event | Raised when |
|---|---|
| `EventCreated` | A new event is created |
| `EventPublished` | Event transitions Draft → Published |
| `EventCancelled` | Event is cancelled |
| `TicketCategoryCreated` | A ticket category is added |
| `TicketCategoryDisabled` | A ticket category is disabled |
| `TicketReserved` | A booking is created |
| `BookingPaid` | A booking is paid |
| `BookingExpired` | A booking expires |
| `TicketCheckedIn` | A ticket is checked in |
| `RefundRequested` | A refund is requested |
| `RefundApproved` | A refund is approved |
| `RefundRejected` | A refund is rejected |
| `RefundPaidOut` | A refund is paid out |
