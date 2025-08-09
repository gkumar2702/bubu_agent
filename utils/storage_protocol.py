"""Storage protocol implementation for Bubu Agent."""

from __future__ import annotations

from datetime import date
from typing import Optional

from .storage import Storage
from .types import MessageType, StorageProtocol


class StorageProtocolImpl(StorageProtocol):
    """Implementation of the storage protocol."""
    
    def __init__(self, storage: Optional[Storage] = None):
        """Initialize with optional storage instance."""
        self.storage = storage
    
    def is_message_sent(self, date_obj: date, message_type: MessageType) -> bool:
        """Check if a message was already sent for the given date and type."""
        if not self.storage:
            return False
        
        try:
            return self.storage.is_message_sent(date_obj, message_type.value)
        except Exception:
            # If storage fails, assume message not sent
            return False
