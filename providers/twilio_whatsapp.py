"""Twilio WhatsApp provider implementation."""

from typing import Optional

import httpx
from utils import get_logger, mask_phone_number, scrub_secrets_from_logs

from .messenger import Messenger

logger = get_logger(__name__)


class TwilioWhatsApp(Messenger):
    """Twilio WhatsApp messaging provider."""
    
    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        base_url: str = "https://api.twilio.com"
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            auth=(account_sid, auth_token),
            timeout=30.0
        )
    
    async def send_text(self, to: str, body: str) -> Optional[str]:
        """
        Send a WhatsApp message via Twilio.
        
        Args:
            to: Recipient phone number in E.164 format
            body: Message text content
            
        Returns:
            Twilio message SID if successful, None otherwise
        """
        try:
            # Ensure WhatsApp format for recipient
            if not to.startswith("whatsapp:"):
                to = f"whatsapp:{to}"
            
            payload = {
                "From": self.from_number,
                "To": to,
                "Body": body
            }
            
            logger.info(
                "Sending WhatsApp message via Twilio",
                to=mask_phone_number(to),
                from_number=mask_phone_number(self.from_number),
                body_length=len(body)
            )
            
            response = await self.client.post(
                f"{self.base_url}/2010-04-01/Accounts/{self.account_sid}/Messages.json",
                data=payload
            )
            
            if response.status_code == 201:
                result = response.json()
                message_sid = result.get("sid")
                
                logger.info(
                    "WhatsApp message sent successfully via Twilio",
                    message_sid=message_sid,
                    to=mask_phone_number(to),
                    status=result.get("status")
                )
                
                return message_sid
            else:
                logger.error(
                    "Failed to send WhatsApp message via Twilio",
                    status_code=response.status_code,
                    response_text=response.text[:200],
                    to=mask_phone_number(to)
                )
                return None
                
        except Exception as e:
            logger.error(
                "Exception sending WhatsApp message via Twilio",
                error=str(e),
                to=mask_phone_number(to)
            )
            return None
    
    async def is_available(self) -> bool:
        """Check if Twilio service is available."""
        try:
            response = await self.client.get(
                f"{self.base_url}/2010-04-01/Accounts/{self.account_sid}.json"
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(
                "Failed to check Twilio availability",
                error=str(e)
            )
            return False
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "twilio"
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def __repr__(self):
        return f"TwilioWhatsApp(from={mask_phone_number(self.from_number)})"
