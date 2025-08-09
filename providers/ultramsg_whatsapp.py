"""Ultramsg WhatsApp provider for Bubu Agent."""

import httpx
from typing import Optional
from .messenger import Messenger
from utils import get_logger

logger = get_logger(__name__)


class UltramsgWhatsApp(Messenger):
    """Ultramsg WhatsApp implementation."""
    
    def __init__(self, api_key: str, instance_id: str):
        """
        Initialize Ultramsg WhatsApp provider.
        
        Args:
            api_key: Your Ultramsg API key
            instance_id: Your Ultramsg instance ID
        """
        self.api_key = api_key
        self.instance_id = instance_id
        self.base_url = "https://api.ultramsg.com"
        
    async def send_text(self, to: str, body: str) -> Optional[str]:
        """Send a text message via Ultramsg."""
        try:
            # Remove any 'whatsapp:' prefix from the number
            to = to.replace('whatsapp:', '')
            
            # Ensure number starts with country code
            if not to.startswith('+'):
                to = '+' + to
            
            url = f"{self.base_url}/{self.instance_id}/messages/chat"
            
            payload = {
                "token": self.api_key,
                "to": to,
                "body": body
            }
            
            logger.info(
                "Sending WhatsApp message via Ultramsg",
                to=to,
                body_length=len(body)
            )
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30.0)
                
                if response.status_code == 200:
                    data = response.json()
                    message_id = data.get('id')
                    
                    logger.info(
                        "WhatsApp message sent successfully via Ultramsg",
                        to=to,
                        message_id=message_id
                    )
                    
                    return message_id
                else:
                    logger.error(
                        "Failed to send WhatsApp message via Ultramsg",
                        status_code=response.status_code,
                        response_text=response.text,
                        to=to
                    )
                    return None
                    
        except Exception as e:
            logger.error(
                "Error sending WhatsApp message via Ultramsg",
                to=to,
                error=str(e)
            )
            return None
    
    async def is_available(self) -> bool:
        """Check if Ultramsg service is available."""
        try:
            url = f"{self.base_url}/{self.instance_id}/instance/connectionState"
            
            payload = {
                "token": self.api_key
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    state = data.get('state')
                    return state == 'open'
                else:
                    logger.warning(
                        "Could not check Ultramsg connection state",
                        status_code=response.status_code
                    )
                    return False
                    
        except Exception as e:
            logger.error(
                "Error checking Ultramsg availability",
                error=str(e)
            )
            return False
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "ultramsg"
