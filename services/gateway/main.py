import os
import httpx
from fastapi import FastAPI, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr
from typing import Optional

from services.notification.publisher import publish_event

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth:8001")

app = FastAPI(title="API Gateway", version="1.0.0")

class EventDispatchPayload(BaseModel):
    event_type: str  # e.g., "user.registered" or "security.alert"
    email: EmailStr
    phone: Optional[str] = None
    details: dict = {}

async def verify_jwt_with_auth_service(authorization: str = Header(...)):
    """Proxies authorization token to Central Auth Service for verification."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/verify",
                headers={"Authorization": authorization}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired access token"
                )
            return response.json()
        except httpx.RequestError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Central Auth Service unavailable"
            )

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "API Gateway"}

@app.post("/events/publish", status_code=status.HTTP_202_ACCEPTED, tags=["Event Dispatcher"])
def dispatch_event(
    payload: EventDispatchPayload,
    user_data: dict = Depends(verify_jwt_with_auth_service)
):
    """
    Protected Endpoint: Receives event request, verifies JWT, 
    and publishes event payload to RabbitMQ event bus.
    """
    try:
        event_data = {
            "email": payload.email,
            "phone": payload.phone,
            "triggered_by": user_data.get("username"),
            "details": payload.details
        }
        
        # Publish asynchronously to RabbitMQ
        publish_event(event_type=payload.event_type, payload=event_data)
        
        return {
            "status": "accepted",
            "message": f"Event '{payload.event_type}' dispatched to message broker.",
            "dispatched_by": user_data.get("username")
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish event to message broker: {str(exc)}"
        )
