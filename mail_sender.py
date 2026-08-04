import os
import smtplib
import logging
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Tuple
from config import Config

logger = logging.getLogger("MailSender")

class EmailSender:
    """SMTP Email Sender supporting HTML bodies, attachments, threading headers, and TLS/SSL encryption."""

    def __init__(self,
                 smtp_server: Optional[str] = None,
                 smtp_port: Optional[int] = None,
                 use_tls: Optional[bool] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 sender_email: Optional[str] = None):
        self.smtp_server = smtp_server or Config.SMTP_SERVER
        self.smtp_port = smtp_port or Config.SMTP_PORT
        self.use_tls = use_tls if use_tls is not None else Config.SMTP_USE_TLS
        self.username = username or Config.SMTP_USERNAME
        self.password = password if password is not None else Config.SMTP_PASSWORD
        self.sender_email = sender_email or Config.SENDER_EMAIL or self.username

    def send_email(self,
                   recipients: List[str],
                   subject: str,
                   html_content: str,
                   text_content: Optional[str] = None,
                   attachment_paths: Optional[List[str]] = None,
                   in_reply_to: Optional[str] = None,
                   references: Optional[List[str]] = None,
                   message_id: Optional[str] = None) -> Tuple[bool, str]:
        """Sends HTML email to recipients with optional attachments and email threading support."""
        if not recipients:
            logger.error("No recipient email addresses provided.")
            return False, ""

        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = ", ".join(recipients)

        current_msg_id = message_id or email.utils.make_msgid(domain="schnelliot.in")
        msg["Message-ID"] = current_msg_id

        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            logger.info(f"Thread header added: In-Reply-To = {in_reply_to}")
        if references:
            msg["References"] = " ".join(references)
            logger.info(f"Thread header added: References = {len(references)} parent IDs")

        # Create alternative part for Body (text + html)
        body_part = MIMEMultipart("alternative")
        plain_text = text_content or "Please enable HTML view to view the BBMP Daily Ticket Dashboard."
        body_part.attach(MIMEText(plain_text, "plain", "utf-8"))
        body_part.attach(MIMEText(html_content, "html", "utf-8"))
        msg.attach(body_part)

        # Attachments
        if attachment_paths:
            for path in attachment_paths:
                if os.path.isfile(path):
                    try:
                        with open(path, "rb") as f:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename={os.path.basename(path)}",
                        )
                        msg.attach(part)
                        logger.info(f"Attached file: {path}")
                    except Exception as e:
                        logger.error(f"Failed to attach file {path}: {e}")
                else:
                    logger.warning(f"Attachment file not found: {path}")

        logger.info(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}...")
        try:
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=25)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=25)
                if self.use_tls:
                    server.starttls()

            if self.username and self.password:
                server.login(self.username, self.password)

            server.sendmail(self.sender_email, recipients, msg.as_string())
            server.quit()
            logger.info(f"Successfully sent email '{subject}' (ID: {current_msg_id}) to {len(recipients)} recipients.")
            return True, current_msg_id

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Failed: Check username/app-password. Error: {e}")
            return False, ""
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False, ""
