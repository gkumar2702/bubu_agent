"""FastAPI application for Bubu Agent."""

import asyncio
from datetime import date
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from utils import (
    config,
    MessageScheduler,
    Storage,
    get_logger,
    setup_logging
)
from utils.compose_refactored import create_message_composer_refactored
from utils.types import MessageType
from providers.huggingface_llm import HuggingFaceLLM
from providers.local_transformers_llm import LocalTransformersLLM

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

# Create scheduler instance
scheduler = MessageScheduler()

# Create LLM instance
# Allow switching to local transformers by environment flag
use_local = False
try:
    import os
    use_local = os.getenv("USE_LOCAL_LLM", "false").lower() in ("1", "true", "yes")
except Exception:
    use_local = False

if use_local:
    # Allow YAML override for model id
    _model_id = config.get_hf_setting("model_id", config.settings.hf_model_id) or config.settings.hf_model_id
    llm = LocalTransformersLLM(model_id=_model_id)
    logger.info("Using LocalTransformersLLM", model_id=_model_id)
else:
    _model_id = config.get_hf_setting("model_id", config.settings.hf_model_id) or config.settings.hf_model_id
    llm = HuggingFaceLLM(
        api_key=config.settings.hf_api_key,
        model_id=_model_id
    )
    logger.info("Using HuggingFaceLLM", model_id=_model_id)


class MessagePreviewRequest(BaseModel):
    """Request model for message preview."""
    type: str
    options: Optional[Dict] = None


class MessagePreviewResponse(BaseModel):
    """Response model for message preview."""
    messages: List[Dict[str, Any]]
    type: str


class SendNowRequest(BaseModel):
    """Request model for sending message now."""
    type: str
    message: Optional[str] = None


class SendNowResponse(BaseModel):
    """Response model for send now."""
    success: bool
    message: str
    provider: Optional[str] = None
    message_id: Optional[str] = None


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
    """Preview messages without sending."""
    try:
        if request.type not in ["morning", "flirty", "night"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message type. Must be one of: morning, flirty, night"
            )
        
        composer = create_message_composer_refactored(llm)
        options = request.options or {}
        count = options.get("count", 1)
        include_fallback = options.get("include_fallback", False)
        randomize = options.get("randomize", False)
        use_ai_generation = options.get("use_ai_generation", False)  # New option for AI generation
        
        messages = []
        
        # Generate multiple messages
        for i in range(count):
            try:
                message_type = MessageType(request.type)
                
                if use_ai_generation:
                    # Use AI generation with Bollywood quotes and cheesy lines
                    today = date.today()
                    result = await composer.compose_message(message_type, today, force_fallback=False)
                    
                    if result.status.value == "ai_generated":
                        messages.append({
                            "text": result.text,
                            "index": i + 1,
                            "is_fallback": False,
                            "is_ai_generated": True,
                            "status": result.status.value
                        })
                    else:
                        # Fallback to template if AI generation fails
                        message = composer.get_message_preview(message_type, {
                            "randomize": randomize,
                            "seed": i if randomize else None
                        })
                        messages.append({
                            "text": message,
                            "index": i + 1,
                            "is_fallback": False,
                            "is_ai_generated": False,
                            "status": "fallback"
                        })
                else:
                    # Use template-based preview (default behavior)
                    message = composer.get_message_preview(message_type, {
                        "randomize": randomize,
                        "seed": i if randomize else None
                    })
                    
                    messages.append({
                        "text": message,
                        "index": i + 1,
                        "is_fallback": False,
                        "is_ai_generated": False,
                        "status": "template"
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to generate message {i+1}", error=str(e))
                continue
        
        # Add fallback templates if requested
        if include_fallback:
            fallback_templates = composer.get_fallback_templates(message_type)
            for i, template in enumerate(fallback_templates[:3]):  # Limit to 3 fallbacks
                messages.append({
                    "text": template,
                    "index": len(messages) + 1,
                    "is_fallback": True,
                    "is_ai_generated": False,
                    "status": "fallback_template"
                })
        
        return MessagePreviewResponse(
            messages=messages,
            type=request.type
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to preview messages", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview messages"
        )


@app.get("/dry-run", response_model=DryRunResponse)
async def dry_run():
    """Get today's planned messages without sending."""
    try:
        today = date.today()
        composer = create_message_composer_refactored(llm, scheduler.storage)
        
        messages = []
        for message_type_str in ["morning", "flirty", "night"]:
            message_type = MessageType(message_type_str)
            result = await composer.compose_message(message_type, today)
            messages.append({
                "type": message_type_str,
                "message": result.text,
                "status": result.status.value
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
        
        if request.message:
            # Send custom message
            success, result_message, provider_info = await scheduler.send_custom_message(request.type, request.message)
        else:
            # Generate and send message
        success, result_message, provider_info = await scheduler.send_message_now_with_info(request.type)
        
        return SendNowResponse(
            success=success,
            message=result_message,
            provider=provider_info.get("provider") if provider_info else None,
            message_id=provider_info.get("message_id") if provider_info else None
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
