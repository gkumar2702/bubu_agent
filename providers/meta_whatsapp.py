"""Meta WhatsApp Cloud API provider implementation."""

from typing import Optional

import httpx
from utils import get_logger, mask_phone_number

from .messenger import Messenger

logger = get_logger(__name__)


class MetaWhatsApp(Messenger):
    """Meta WhatsApp Cloud API messaging provider."""
    
    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        base_url: str = "https://graph.facebook.com/v18.0"
    ):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=30.0
        )
    
    async def send_text(self, to: str, body: str) -> Optional[str]:
        """
        Send a WhatsApp message via Meta Cloud API.
        
        Args:
            to: Recipient phone number in E.164 format
            body: Message text content
            
        Returns:
            Meta message ID if successful, None otherwise
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {
                    "body": body
                }
            }
            
            logger.info(
                "Sending WhatsApp message via Meta",
                to=mask_phone_number(to),
                phone_number_id=self.phone_number_id,
                body_length=len(body)
            )
            
            response = await self.client.post(
                f"{self.base_url}/{self.phone_number_id}/messages",
                json=payload,
                params={"access_token": self.access_token}
            )
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get("messages", [{}])[0].get("id")
                
                logger.info(
                    "WhatsApp message sent successfully via Meta",
                    message_id=message_id,
                    to=mask_phone_number(to)
                )
                
                return message_id
            else:
                logger.error(
                    "Failed to send WhatsApp message via Meta",
                    status_code=response.status_code,
                    response_text=response.text[:200],
                    to=mask_phone_number(to)
                )
                return None
                
        except Exception as e:
            logger.error(
                "Exception sending WhatsApp message via Meta",
                error=str(e),
                to=mask_phone_number(to)
            )
            return None
    
    async def is_available(self) -> bool:
        """Check if Meta WhatsApp service is available."""
        try:
            response = await self.client.get(
                f"{self.base_url}/{self.phone_number_id}",
                params={"access_token": self.access_token}
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(
                "Failed to check Meta WhatsApp availability",
                error=str(e)
            )
            return False
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "meta"
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def __repr__(self):
        return f"MetaWhatsApp(phone_number_id={self.phone_number_id})"
