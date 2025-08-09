"""Database storage for Bubu Agent."""

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from utils import get_logger

logger = get_logger(__name__)


class MessageRecord:
    """Record of a sent message."""
    
    def __init__(
        self,
        date: date,
        slot: str,
        text: str,
        status: str,
        provider_id: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.date = date
        self.slot = slot
        self.text = text
        self.status = status
        self.provider_id = provider_id
        self.created_at = created_at or datetime.now()
    
    def __repr__(self):
        return f"MessageRecord(date={self.date}, slot={self.slot}, status={self.status})"


class Storage:
    """SQLite storage for message tracking."""
    
    def __init__(self, db_path: str = "bubu_agent.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages_sent (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    slot TEXT NOT NULL,
                    text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provider_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, slot)
                )
            """)
            
            # Create table for song recommendations
            conn.execute("""
                CREATE TABLE IF NOT EXISTS song_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    slot TEXT NOT NULL,
                    song_id TEXT NOT NULL,
                    song_title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for faster lookups
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_date_slot 
                ON messages_sent(date, slot)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_song_reco_date_slot 
                ON song_recommendations(date, slot)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_song_reco_song_id 
                ON song_recommendations(song_id)
            """)
            
            conn.commit()
            logger.info("Database initialized", db_path=str(self.db_path))
    
    def record_message_sent(
        self,
        date_obj: date,
        slot: str,
        text: str,
        status: str = "sent",
        provider_id: Optional[str] = None
    ) -> None:
        """Record a message as sent."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO messages_sent 
                    (date, slot, text, status, provider_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    date_obj.isoformat(),
                    slot,
                    text,
                    status,
                    provider_id,
                    datetime.now().isoformat()
                ))
                conn.commit()
                
            logger.info(
                "Message recorded",
                date=date_obj.isoformat(),
                slot=slot,
                status=status,
                provider_id=provider_id
            )
            
        except Exception as e:
            logger.error(
                "Failed to record message",
                date=date_obj.isoformat(),
                slot=slot,
                error=str(e)
            )
            raise
    
    def is_message_sent(self, date_obj: date, slot: str) -> bool:
        """Check if a message was already sent for a given date and slot."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM messages_sent 
                    WHERE date = ? AND slot = ? AND status = 'sent'
                """, (date_obj.isoformat(), slot))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            logger.error(
                "Failed to check message status",
                date=date_obj.isoformat(),
                slot=slot,
                error=str(e)
            )
            return False
    
    def get_messages_for_date(self, date_obj: date) -> List[MessageRecord]:
        """Get all messages sent for a specific date."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT date, slot, text, status, provider_id, created_at
                    FROM messages_sent 
                    WHERE date = ?
                    ORDER BY created_at
                """, (date_obj.isoformat(),))
                
                records = []
                for row in cursor.fetchall():
                    record = MessageRecord(
                        date=date.fromisoformat(row[0]),
                        slot=row[1],
                        text=row[2],
                        status=row[3],
                        provider_id=row[4],
                        created_at=datetime.fromisoformat(row[5])
                    )
                    records.append(record)
                
                return records
                
        except Exception as e:
            logger.error(
                "Failed to get messages for date",
                date=date_obj.isoformat(),
                error=str(e)
            )
            return []
    
    def get_message_status(self, date_obj: date, slot: str) -> Optional[str]:
        """Get the status of a message for a given date and slot."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT status FROM messages_sent 
                    WHERE date = ? AND slot = ?
                """, (date_obj.isoformat(), slot))
                
                row = cursor.fetchone()
                return row[0] if row else None
                
        except Exception as e:
            logger.error(
                "Failed to get message status",
                date=date_obj.isoformat(),
                slot=slot,
                error=str(e)
            )
            return None
    
    def update_message_status(
        self,
        date_obj: date,
        slot: str,
        status: str,
        provider_id: Optional[str] = None
    ) -> bool:
        """Update the status of a message."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if provider_id:
                    conn.execute("""
                        UPDATE messages_sent 
                        SET status = ?, provider_id = ?
                        WHERE date = ? AND slot = ?
                    """, (status, provider_id, date_obj.isoformat(), slot))
                else:
                    conn.execute("""
                        UPDATE messages_sent 
                        SET status = ?
                        WHERE date = ? AND slot = ?
                    """, (status, date_obj.isoformat(), slot))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(
                "Failed to update message status",
                date=date_obj.isoformat(),
                slot=slot,
                status=status,
                error=str(e)
            )
            return False
    
    def get_recent_messages(self, days: int = 7) -> List[MessageRecord]:
        """Get messages from the last N days."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT date, slot, text, status, provider_id, created_at
                    FROM messages_sent 
                    WHERE date >= date('now', '-{} days')
                    ORDER BY date DESC, created_at DESC
                """.format(days))
                
                records = []
                for row in cursor.fetchall():
                    record = MessageRecord(
                        date=date.fromisoformat(row[0]),
                        slot=row[1],
                        text=row[2],
                        status=row[3],
                        provider_id=row[4],
                        created_at=datetime.fromisoformat(row[5])
                    )
                    records.append(record)
                
                return records
                
        except Exception as e:
            logger.error(
                "Failed to get recent messages",
                days=days,
                error=str(e)
            )
            return []
    
    def cleanup_old_messages(self, days: int = 90) -> int:
        """Clean up messages older than N days. Returns number of deleted records."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM messages_sent 
                    WHERE date < date('now', '-{} days')
                """.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(
                    "Cleaned up old messages",
                    deleted_count=deleted_count,
                    older_than_days=days
                )
                
                return deleted_count
                
        except Exception as e:
            logger.error(
                "Failed to cleanup old messages",
                days=days,
                error=str(e)
            )
            return 0
    
    def record_song_recommendation(
        self,
        date_obj: date,
        slot: str,
        song_id: str,
        song_title: str
    ) -> None:
        """Record a song recommendation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO song_recommendations 
                    (date, slot, song_id, song_title, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    date_obj.isoformat(),
                    slot,
                    song_id,
                    song_title,
                    datetime.now().isoformat()
                ))
                conn.commit()
                
            logger.info(
                "Song recommendation recorded",
                date=date_obj.isoformat(),
                slot=slot,
                song_id=song_id,
                song_title=song_title
            )
            
        except Exception as e:
            logger.error(f"Failed to record song recommendation: {e}")
    
    def get_recent_song_ids(self, days: int = 30) -> set[str]:
        """Get set of recently recommended song IDs."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT DISTINCT song_id 
                    FROM song_recommendations 
                    WHERE date >= date('now', '-{} days')
                """.format(days))
                
                song_ids = {row[0] for row in cursor.fetchall()}
                
            logger.info(
                "Retrieved recent song IDs",
                count=len(song_ids),
                days=days
            )
            return song_ids
            
        except Exception as e:
            logger.error(f"Failed to get recent song IDs: {e}")
            return set()
