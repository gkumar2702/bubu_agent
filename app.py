"""FastAPI application for Bubu Agent."""

import asyncio
from datetime import date
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from compose import create_message_composer
from config import config
from scheduler import scheduler
from storage import Storage
from utils import get_logger, setup_logging

# Setup logging
setup_logging(config.settings.log_level)
logger = get_logger(__name__)

# FastAPI app
app = FastAPI(
    title="Bubu Agent",
    description="A production-ready Python service that sends personalized WhatsApp messages",
    version="0.1.0"
)

# Security
security = HTTPBearer()


class MessagePreviewRequest(BaseModel):
    """Request model for message preview."""
    type: str
    options: Optional[Dict] = None


class MessagePreviewResponse(BaseModel):
    """Response model for message preview."""
    message: str
    type: str


class SendNowRequest(BaseModel):
    """Request model for sending message now."""
    type: str


class SendNowResponse(BaseModel):
    """Response model for send now."""
    success: bool
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    enabled: bool
    provider: str
    timezone: str


class PlanResponse(BaseModel):
    """Today's plan response."""
    date: str
    morning: Optional[str]
    flirty: Optional[str]
    night: Optional[str]


class DryRunResponse(BaseModel):
    """Dry run response."""
    date: str
    messages: List[Dict[str, str]]


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify the bearer token."""
    if credentials.credentials != config.settings.api_bearer_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token"
        )
    return True


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    try:
        logger.info("Starting Bubu Agent")
        scheduler.start()
        logger.info("Bubu Agent started successfully")
    except Exception as e:
        logger.error("Failed to start Bubu Agent", error=str(e))
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    try:
        logger.info("Shutting down Bubu Agent")
        scheduler.stop()
        logger.info("Bubu Agent shut down successfully")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check if messenger is available
        messenger_available = await scheduler.messenger.is_available()
        
        return HealthResponse(
            status="healthy" if messenger_available else "degraded",
            enabled=config.settings.enabled,
            provider=config.settings.whatsapp_provider,
            timezone=config.settings.timezone
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            enabled=config.settings.enabled,
            provider=config.settings.whatsapp_provider,
            timezone=config.settings.timezone
        )


@app.get("/plan/today", response_model=PlanResponse)
async def get_todays_plan():
    """Get today's planned message times."""
    try:
        plan = scheduler.get_todays_plan()
        today = date.today()
        
        return PlanResponse(
            date=today.isoformat(),
            morning=plan.get("morning"),
            flirty=plan.get("flirty"),
            night=plan.get("night")
        )
    except Exception as e:
        logger.error("Failed to get today's plan", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get today's plan"
        )


@app.post("/config/preview", response_model=MessagePreviewResponse)
async def preview_message(
    request: MessagePreviewRequest,
    _: bool = Depends(verify_token)
):
    """Preview a message without sending."""
    try:
        if request.type not in ["morning", "flirty", "night"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message type. Must be one of: morning, flirty, night"
            )
        
        composer = create_message_composer()
        message = composer.get_message_preview(request.type, request.options)
        
        return MessagePreviewResponse(
            message=message,
            type=request.type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to preview message", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview message"
        )


@app.get("/dry-run", response_model=DryRunResponse)
async def dry_run():
    """Get today's planned messages without sending."""
    try:
        today = date.today()
        composer = create_message_composer()
        composer.set_storage(scheduler.storage)
        
        messages = []
        for message_type in ["morning", "flirty", "night"]:
            message, status = await composer.compose_message(message_type, today)
            messages.append({
                "type": message_type,
                "message": message,
                "status": status
            })
        
        return DryRunResponse(
            date=today.isoformat(),
            messages=messages
        )
    except Exception as e:
        logger.error("Failed to generate dry run", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate dry run"
        )


@app.post("/send-now", response_model=SendNowResponse)
async def send_message_now(
    request: SendNowRequest,
    _: bool = Depends(verify_token)
):
    """Send a message immediately."""
    try:
        if request.type not in ["morning", "flirty", "night"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message type. Must be one of: morning, flirty, night"
            )
        
        success, message = await scheduler.send_message_now(request.type)
        
        return SendNowResponse(
            success=success,
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to send message now", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


@app.post("/pause")
async def pause_agent(_: bool = Depends(verify_token)):
    """Pause the agent (disable it)."""
    try:
        # This would require updating the config and restarting
        # For now, we'll just return a message
        return {"message": "Agent paused. Set ENABLED=false in .env to disable permanently."}
    except Exception as e:
        logger.error("Failed to pause agent", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause agent"
        )


@app.get("/messages/recent")
async def get_recent_messages(
    days: int = 7,
    _: bool = Depends(verify_token)
):
    """Get recent messages from the last N days."""
    try:
        if days < 1 or days > 30:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Days must be between 1 and 30"
            )
        
        messages = scheduler.storage.get_recent_messages(days)
        
        return {
            "days": days,
            "messages": [
                {
                    "date": msg.date.isoformat(),
                    "slot": msg.slot,
                    "text": msg.text,
                    "status": msg.status,
                    "provider_id": msg.provider_id,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get recent messages", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recent messages"
        )


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "name": "Bubu Agent",
        "version": "0.1.0",
        "description": "A production-ready Python service that sends personalized WhatsApp messages",
        "endpoints": {
            "health": "/healthz",
            "plan": "/plan/today",
            "dry_run": "/dry-run",
            "send_now": "/send-now",
            "preview": "/config/preview",
            "recent_messages": "/messages/recent"
        }
    }


def main():
    """Main function to run the application."""
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=config.settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
