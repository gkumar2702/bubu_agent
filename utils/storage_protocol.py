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
    
    def record_song_recommendation(self, date_obj: date, slot: str, song_id: str, song_title: str) -> None:
        """Record a song recommendation."""
        if not self.storage:
            return
        
        try:
            self.storage.record_song_recommendation(date_obj, slot, song_id, song_title)
        except Exception:
            # If storage fails, silently continue
            pass
    
    def get_recent_song_ids(self, days: int = 30) -> set[str]:
        """Get set of recently recommended song IDs."""
        if not self.storage:
            return set()
        
        try:
            return self.storage.get_recent_song_ids(days)
        except Exception:
            # If storage fails, return empty set
            return set()
