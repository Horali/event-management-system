from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.api.v1.routes.events import router as events_router
from src.api.v1.routes.bookings import router as bookings_router
from src.api.v1.routes.refunds import router as refunds_router
from src.api.v1.routes.tickets import router as tickets_router
from src.application.exceptions import NotFoundException, BusinessRuleException, ApplicationException

app = FastAPI(
    title="Event Management System API",
    description="REST API for the Event Ticketing & Booking System following Clean Architecture and DDD principles",
    version="1.0.0",
)

# Global Exception Handlers
@app.exception_handler(NotFoundException)
def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=404,
        content={"error": "NotFound", "message": exc.message}
    )

@app.exception_handler(BusinessRuleException)
def business_rule_exception_handler(request: Request, exc: BusinessRuleException):
    return JSONResponse(
        status_code=400,
        content={"error": "BusinessRuleViolation", "message": exc.message}
    )

@app.exception_handler(ValueError)
def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "InvalidInput", "message": str(exc)}
    )

@app.exception_handler(ApplicationException)
def application_exception_handler(request: Request, exc: ApplicationException):
    return JSONResponse(
        status_code=500,
        content={"error": "ApplicationError", "message": exc.message}
    )

# Register Routers
app.include_router(events_router, prefix="/api/v1")
app.include_router(bookings_router, prefix="/api/v1")
app.include_router(refunds_router, prefix="/api/v1")
app.include_router(tickets_router, prefix="/api/v1")

@app.get("/")
def home():
    return {
        "message": "Welcome to Event Management System API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }