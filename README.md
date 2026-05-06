# Event Management System

## Project Overview
The Event Management System is a backend REST API developed to facilitate event ticketing and booking. This project implements Clean Architecture and Domain-Driven Design (DDD) principles to ensure clear separation between domain logic, application use cases, infrastructure, and presentation layers.

It allows Event Organizers to create and manage events, Customers to book and pay for tickets, and Gate Officers to validate tickets during check-in.

## Prerequisites
Before you begin, ensure you have the following installed on your local machine:
- **Python 3.10+**
- **uv** (for fast dependency management)
- **PostgreSQL** (version 13 or higher recommended)

## Setup Guide

Follow these steps to set up the project locally:

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd event-management-system
   ```

2. **Install Dependencies:**
   This project uses `uv` for dependency management. To install the required packages and create the virtual environment, run:
   ```bash
   uv sync
   ```

3. **Environment Configuration:**
   Copy the example environment variables file and configure it with your local credentials.
   ```bash
   cp .env.example .env
   ```
   *Note: Ensure your `.env` is never committed to version control. It should be listed in your `.gitignore`.*

## Configuring and Running PostgreSQL Locally

This project uses PostgreSQL for data persistence. To set up the database:

1. **Start PostgreSQL:** Ensure your local PostgreSQL service is running.
2. **Create a Database:** Use a database client (like pgAdmin, DBeaver) or the `psql` command line tool to create a new database for the project:
   ```sql
   CREATE DATABASE event_management_db;
   ```
3. **Configure Database URL:** Open your `.env` file and update the `DATABASE_URL` variable to point to your local PostgreSQL instance. The standard format using the `psycopg` driver is:
   ```env
   DATABASE_URL=postgresql+psycopg://<username>:<password>@localhost:5432/event_management_db
   ```
   *(Replace `<username>` and `<password>` with your actual PostgreSQL credentials).*

## Running the Application

Once the database is configured and dependencies are installed, you can start the FastAPI development server:

```bash
uv run uvicorn src.main:app --reload
```

The server will be running at `http://127.0.0.1:8000`. You can access the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.