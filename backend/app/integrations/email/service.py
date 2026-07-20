import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("email_service")


class EmailService:

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL

    def _configured(self) -> bool:
        return bool(self.username and self.password)

    def send(self, to_email: str, subject: str, html_body: str) -> bool:
        if not self._configured():
            logger.info("SMTP not configured; email not sent to=%s subject=%s", to_email, subject)
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.from_email, [to_email], msg.as_string())
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send email to %s: %s", to_email, exc)
            return False


email_service = EmailService()
