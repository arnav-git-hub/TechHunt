"""Async email delivery service for Stage 6 notifications.

Uses aiosmtplib when SMTP_HOST is configured. When the host is not set
the service is a no-op so the application starts cleanly without SMTP.
Email bodies are intentionally plain-text to maximise deliverability and
avoid HTML injection concerns.
"""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Send transactional emails via async SMTP.

    All methods are safe to call unconditionally: if SMTP is not configured
    they log a debug message and return without raising.
    """

    @property
    def is_configured(self) -> bool:
        """True when a SMTP host and sender address are both set."""
        return bool(settings.smtp_host and settings.smtp_from_email)

    async def send(self, *, to: str, subject: str, body: str) -> None:
        """Send one plain-text email.

        Args:
            to: Recipient email address.
            subject: Email subject line.
            body: Plain-text message body.
        """
        if not self.is_configured:
            logger.debug(
                "EmailService: SMTP not configured — skipping email to %s (subject: %s)",
                to,
                subject,
            )
            return

        try:
            import aiosmtplib  # imported lazily so the app starts without the package installed
            from email.mime.text import MIMEText

            message = MIMEText(body, "plain", "utf-8")
            message["From"] = settings.smtp_from_email
            message["To"] = to
            message["Subject"] = subject

            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username or None,
                password=settings.smtp_password or None,
                use_tls=settings.smtp_use_tls,
            )
            logger.info("EmailService: sent email to %s (subject: %s)", to, subject)
        except Exception as exc:  # noqa: BLE001
            # Email delivery failure must never crash the application.
            logger.error("EmailService: failed to send to %s — %s", to, exc)

    async def send_event_reminder(self, *, to: str, event_title: str, remind_at: str) -> None:
        """Send a reminder email for a specific event.

        Args:
            to: Recipient email address.
            event_title: Human-readable event name.
            remind_at: ISO 8601 string of the scheduled reminder time (UTC).
        """
        subject = f"Reminder: {event_title}"
        body = (
            f"Hi,\n\n"
            f"This is your scheduled reminder for:\n\n"
            f"  {event_title}\n\n"
            f"Reminder scheduled at: {remind_at} UTC\n\n"
            f"Visit TechHunt to view full event details.\n\n"
            f"— The TechHunt Team\n\n"
            f"---\n"
            f"You received this because you requested an email reminder on TechHunt.\n"
            f"To cancel future reminders, visit the event page and click 'Cancel reminder'.\n"
        )
        await self.send(to=to, subject=subject, body=body)
