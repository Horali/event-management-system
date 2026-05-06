# Documentation

## 1. Initial Business Rules

The following business rules have been derived from the user stories and acceptance criteria defined in the Case Study:

### Event Management Rules
- **Event Creation**: An event's end date cannot be earlier than its start date. The maximum capacity must be greater than zero. A newly created event defaults to the `Draft` status.
- **Event Publishing**: An event can only be published if it has at least one active ticket category, and the total ticket quota across all categories does not exceed the maximum event capacity. Only `Draft` events can be published; `Cancelled` events cannot.
- **Event Cancellation**: An event with the `Published` status can be cancelled, but a `Completed` event cannot. Cancelling an event disables all ticket sales, and any paid bookings are marked as requiring a refund.

### Ticket Category Rules
- **Category Creation**: The ticket price cannot be less than zero (free tickets are allowed but not negative), and the quota must be greater than zero. The sales period for a category must end before or at the event start date. The total quota of all ticket categories combined must not exceed the maximum capacity of the event.
- **Category Disabling**: Ticket categories can be disabled as long as the event has not been completed. Disabled categories cannot be purchased, but any existing bookings under that category are preserved for historical purposes.

### Booking and Payment Rules
- **Booking Creation**: Bookings can only be created for `Published` events and active ticket categories, and only within the active sales period. The quantity must be greater than zero and cannot exceed the remaining ticket quota. A customer can only have one active booking per event at a time. A new booking defaults to `PendingPayment` status and has a strict payment deadline (e.g., 15 minutes).
- **Pricing**: The total booking price is calculated as (ticket unit price * ticket quantity) + service fee (if applicable). The total price must never be negative and is represented as a `Money` value object.
- **Payment Execution**: Bookings can only be paid if the status is `PendingPayment` and the deadline has not passed. The payment amount must strictly equal the booking total price. Upon success, the booking status changes to `Paid`, and individual tickets with unique codes are issued.
- **Booking Expiration**: Unpaid bookings are marked as `Expired` automatically once the payment deadline passes, and their reserved ticket quota is released back to the available pool.

### Ticket and Check-in Rules
- **Ticket Visibility**: Customers can only view tickets linked to `Paid` bookings. Tickets from cancelled events must show `Cancelled` or `RefundRequired`.
- **Check-in Validation**: A ticket can only be checked in for the exact event it belongs to. The ticket status must be `Active`. Tickets already checked-in cannot be used again. Check-in must occur on the event day or within the allowed time window. Upon successful check-in, the ticket status changes to `CheckedIn`.
- **Invalid Tickets**: Fake, duplicated, non-matching events, or tickets for cancelled events must be rejected during the check-in process without altering the ticket's status.

### Refund Rules
- **Refund Eligibility**: Refunds can only be requested for `Paid` bookings, before the refund deadline, and provided no tickets from the booking have been checked in. Cancelled events automatically authorize refunds.
- **Refund Approval**: When a refund is approved by the Organizer, its status changes to `Approved`, the associated tickets are changed to `Cancelled`, and the booking status changes to `Refunded`.
- **Refund Rejection**: Rejected refunds must include a rejection reason. The related booking remains `Paid`, and tickets remain `Active`.
- **Payouts**: System admins mark approved refunds as `PaidOut`, requiring a payment reference. A paid-out refund is final and cannot be modified further.

---

## 2. Initial Domain Model Draft

This section outlines the draft of the domain model using Domain-Driven Design (DDD) tactical patterns.

### Aggregates & Aggregate Roots
- **Event Aggregate (`Event`)**: Acts as the root for event-related data. Responsible for managing its own state (Draft, Published, Cancelled, Completed) and ensuring invariants around its capacity and ticket categories.
- **Booking Aggregate (`Booking`)**: Manages the reservation lifecycle (PendingPayment, Paid, Expired, Refunded). It calculates totals and handles payment deadlines.
- **Refund Aggregate (`Refund`)**: Tracks the lifecycle of a refund request (Requested, Approved, Rejected, PaidOut) independent of the event or booking, enforcing refund rules and holding payment references.

### Entities
- **TicketCategory**: Exists within the boundary of the `Event` aggregate. Has an identity but its lifecycle is tied to the event. Holds price, quota, and sales period data.
- **Ticket**: Exists within the boundary of the `Booking` aggregate, created only after successful payment. Each ticket has a unique identifying code and maintains its own status (Active, CheckedIn, Cancelled).

### Value Objects
- **Money**: Represents an amount and its currency. Ensures calculations (like total price) are handled accurately and prevents negative values.
- **DateTime Range (Sales Period)**: Represents the start and end dates for ticket sales.
- **Booking Status**: Enum value object representing PendingPayment, Paid, Expired, Refunded.
- **Event Status**: Enum value object representing Draft, Published, Cancelled, Completed.

---

## 3. Initial Ubiquitous Language Glossary

| Term | Meaning |
|---|---|
| **Event** | An activity organized by an Event Organizer and attended by customers. |
| **Event Organizer** | A user who creates and manages events. |
| **Customer** | A user who books and purchases tickets. |
| **Gate Officer** | A user who validates tickets during event check-in. |
| **Ticket Category** | A type of ticket, such as Regular, VIP, or Early Bird. |
| **Quota** | The maximum number of tickets available in a ticket category. |
| **Booking** | A temporary reservation before payment is completed. |
| **Pending Payment** | A booking status indicating that payment has not been completed. |
| **Paid** | A booking status indicating that payment has been completed. |
| **Expired** | A booking status indicating that the payment deadline has passed. |
| **Ticket** | Proof of attendance generated after a booking is paid. |
| **Ticket Code** | A unique code used to identify and validate a ticket. |
| **Check-in** | The process of validating a ticket when a participant enters the event venue. |
| **Refund** | The process of returning money to a customer. |
| **Money** | A value object representing an amount and currency. |
| **Sales Period** | The period during which a ticket category can be purchased. |
| **Payment Deadline** | The deadline for completing payment after a booking is created. |
