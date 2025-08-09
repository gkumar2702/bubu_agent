"""Scheduler for Bubu Agent message delivery."""

import asyncio
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from compose import MessageComposer, create_message_composer
from config import config
from providers import TwilioWhatsApp, MetaWhatsApp
from storage import Storage
from utils import (
    SeededRandom, get_date_seed, get_logger,
    get_timezone_aware_datetime, is_within_time_window
)

logger = get_logger(__name__)


class MessageScheduler:
    """Handles scheduling and sending of messages."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.storage = Storage()
        self.composer = create_message_composer()
        self.messenger = self._create_messenger()
        
        # Set storage reference in composer
        self.composer.set_storage(self.storage)
        
        # Message windows (in local timezone)
        self.message_windows = {
            "morning": (time(6, 45), time(9, 30)),
            "flirty": (time(12, 0), time(17, 30)),
            "night": (time(21, 30), time(23, 30))
        }
        
        # Do not disturb window (except night slot)
        self.dnd_start = time(23, 45)
        self.dnd_end = time(6, 30)
    
    def _create_messenger(self):
        """Create the appropriate messenger based on configuration."""
        settings = config.settings
        
        if settings.whatsapp_provider == "twilio":
            if not all([settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_whatsapp_from]):
                raise ValueError("Missing Twilio configuration")
            
            return TwilioWhatsApp(
                account_sid=settings.twilio_account_sid,
                auth_token=settings.twilio_auth_token,
                from_number=settings.twilio_whatsapp_from
            )
        
        elif settings.whatsapp_provider == "meta":
            if not all([settings.meta_access_token, settings.meta_phone_number_id]):
                raise ValueError("Missing Meta configuration")
            
            return MetaWhatsApp(
                access_token=settings.meta_access_token,
                phone_number_id=settings.meta_phone_number_id
            )
        
        else:
            raise ValueError(f"Unsupported WhatsApp provider: {settings.whatsapp_provider}")
    
    def start(self):
        """Start the scheduler."""
        if not config.settings.enabled:
            logger.info("Bubu Agent is disabled")
            return
        
        # Schedule daily planning job at 00:05
        self.scheduler.add_job(
            self._plan_daily_messages,
            CronTrigger(hour=0, minute=5, timezone=config.settings.timezone),
            id="daily_planning",
            name="Daily Message Planning"
        )
        
        # Schedule cleanup job weekly
        self.scheduler.add_job(
            self._cleanup_old_messages,
            CronTrigger(day_of_week="sun", hour=2, minute=0, timezone=config.settings.timezone),
            id="cleanup",
            name="Cleanup Old Messages"
        )
        
        # Plan messages for today if scheduler starts after 00:05
        asyncio.create_task(self._plan_daily_messages())
        
        self.scheduler.start()
        logger.info("Message scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Message scheduler stopped")
    
    async def _plan_daily_messages(self):
        """Plan and schedule messages for the current day."""
        try:
            today = date.today()
            
            # Check if today is a skip date
            skip_dates = config.settings.get_skip_dates_list()
            if today in skip_dates:
                logger.info("Today is a skip date, no messages scheduled", date=today.isoformat())
                return
            
            # Remove existing jobs for today
            self._remove_todays_jobs()
            
            # Generate times for each message type
            message_times = self._generate_daily_times(today)
            
            # Schedule jobs
            for message_type, send_time in message_times.items():
                if send_time:
                    job_id = f"{today.isoformat()}_{message_type}"
                    
                    self.scheduler.add_job(
                        self._send_message,
                        "date",
                        run_date=send_time,
                        args=[message_type, today],
                        id=job_id,
                        name=f"{message_type.capitalize()} Message"
                    )
                    
                    logger.info(
                        "Scheduled message",
                        date=today.isoformat(),
                        type=message_type,
                        time=send_time.strftime("%H:%M"),
                        job_id=job_id
                    )
            
        except Exception as e:
            logger.error("Error planning daily messages", error=str(e))
    
    def _generate_daily_times(self, date_obj: date) -> Dict[str, Optional[datetime]]:
        """Generate randomized times for each message type on a given date."""
        # Use seeded random for consistent times per day
        seed = get_date_seed(date_obj)
        rng = SeededRandom(seed)
        
        times = {}
        tz = timezone(config.settings.timezone)
        
        for message_type, (start_time, end_time) in self.message_windows.items():
            # Generate random time within window
            start_minutes = start_time.hour * 60 + start_time.minute
            end_minutes = end_time.hour * 60 + end_time.minute
            
            if end_minutes < start_minutes:  # Window spans midnight
                end_minutes += 24 * 60
            
            random_minutes = rng.randint(start_minutes, end_minutes)
            
            # Add jitter (±20 minutes)
            jitter = rng.randint(-20, 20)
            random_minutes += jitter
            
            # Normalize to 24-hour format
            random_minutes = max(0, min(random_minutes, 24 * 60 - 1))
            
            # Convert to datetime
            hour = random_minutes // 60
            minute = random_minutes % 60
            
            # Create datetime in target timezone
            dt = datetime.combine(date_obj, time(hour, minute))
            dt = tz.localize(dt)
            
            # Check if time is within do not disturb window (except night slot)
            if message_type != "night":
                current_time = dt.time()
                if is_within_time_window(current_time, self.dnd_start, self.dnd_end):
                    logger.warning(
                        "Generated time falls in DND window, skipping",
                        message_type=message_type,
                        time=dt.strftime("%H:%M")
                    )
                    times[message_type] = None
                    continue
            
            times[message_type] = dt
        
        return times
    
    def _remove_todays_jobs(self):
        """Remove existing jobs for today."""
        today = date.today()
        jobs_to_remove = []
        
        for job in self.scheduler.get_jobs():
            if job.id and job.id.startswith(today.isoformat()):
                jobs_to_remove.append(job.id)
        
        for job_id in jobs_to_remove:
            self.scheduler.remove_job(job_id)
            logger.debug("Removed existing job", job_id=job_id)
    
    async def _send_message(self, message_type: str, date_obj: date):
        """Send a message for the given type and date."""
        try:
            logger.info(
                "Sending scheduled message",
                type=message_type,
                date=date_obj.isoformat()
            )
            
            # Check if already sent
            if self.storage.is_message_sent(date_obj, message_type):
                logger.info(
                    "Message already sent, skipping",
                    type=message_type,
                    date=date_obj.isoformat()
                )
                return
            
            # Compose message
            message, status = await self.composer.compose_message(message_type, date_obj)
            
            if not message:
                logger.warning(
                    "No message composed, skipping",
                    type=message_type,
                    date=date_obj.isoformat(),
                    status=status
                )
                return
            
            # Send message
            provider_id = await self.messenger.send_text(
                config.settings.gf_whatsapp_number,
                message
            )
            
            # Record the message
            self.storage.record_message_sent(
                date_obj=date_obj,
                slot=message_type,
                text=message,
                status="sent" if provider_id else "failed",
                provider_id=provider_id
            )
            
            logger.info(
                "Message sent successfully",
                type=message_type,
                date=date_obj.isoformat(),
                provider_id=provider_id,
                status=status
            )
            
        except Exception as e:
            logger.error(
                "Error sending scheduled message",
                type=message_type,
                date=date_obj.isoformat(),
                error=str(e)
            )
            
            # Record failure
            self.storage.record_message_sent(
                date_obj=date_obj,
                slot=message_type,
                text="",
                status="error",
                provider_id=None
            )
    
    async def send_message_now(self, message_type: str) -> Tuple[bool, str]:
        """Send a message immediately."""
        try:
            today = date.today()
            
            # Check if already sent
            if self.storage.is_message_sent(today, message_type):
                return False, "Message already sent today"
            
            # Compose and send
            message, status = await self.composer.compose_message(message_type, today)
            
            if not message:
                return False, f"No message composed (status: {status})"
            
            provider_id = await self.messenger.send_text(
                config.settings.gf_whatsapp_number,
                message
            )
            
            # Record the message
            self.storage.record_message_sent(
                date_obj=today,
                slot=message_type,
                text=message,
                status="sent" if provider_id else "failed",
                provider_id=provider_id
            )
            
            return True, "Message sent successfully"
            
        except Exception as e:
            logger.error(
                "Error sending message now",
                type=message_type,
                error=str(e)
            )
            return False, f"Error: {str(e)}"
    
    def get_todays_plan(self) -> Dict[str, Optional[str]]:
        """Get today's planned message times."""
        today = date.today()
        times = self._generate_daily_times(today)
        
        plan = {}
        for message_type, dt in times.items():
            if dt:
                plan[message_type] = dt.strftime("%H:%M")
            else:
                plan[message_type] = None
        
        return plan
    
    async def _cleanup_old_messages(self):
        """Clean up old message records."""
        try:
            deleted_count = self.storage.cleanup_old_messages(days=90)
            logger.info("Cleanup completed", deleted_count=deleted_count)
        except Exception as e:
            logger.error("Error during cleanup", error=str(e))


# Global scheduler instance
scheduler = MessageScheduler()
