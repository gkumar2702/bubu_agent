"""Abstract interface for WhatsApp messaging providers."""

from abc import ABC, abstractmethod
from typing import Optional


class Messenger(ABC):
    """Abstract interface for WhatsApp messaging providers."""
    
    @abstractmethod
    async def send_text(self, to: str, body: str) -> Optional[str]:
        """
        Send a text message via WhatsApp.
        
        Args:
            to: Recipient phone number in E.164 format
            body: Message text content
            
        Returns:
            Provider message ID if successful, None otherwise
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the messaging service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the messaging provider.
        
        Returns:
            Provider name (e.g., 'twilio', 'meta')
        """
        pass
