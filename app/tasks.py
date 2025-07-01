from celery import current_app as celery_app
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Listing
import smtplib
from app.config import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText  # Note the correct capitalization


@celery_app.task
def send_email_task(to_email: str, subject: str, body: str):
    try:
        if not settings.smtp_host:
            print("SMTP not configured, skipping email")
            return

        msg = MIMEMultipart()
        msg["From"] = settings.smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))  # Fixed: Changed MimeText to MIMEText

        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port)
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        text = msg.as_string()
        server.sendmail(settings.smtp_user, to_email, text)
        server.quit()

        return "Email sent successfully"
    except Exception as e:
        return f"Email sending failed: {str(e)}"


@celery_app.task
def update_listing_views(listing_id: str):
    db = SessionLocal()
    try:
        listing = db.query(Listing).filter(Listing.id == listing_id).first()
        if listing:
            listing.view_count += 1
            db.commit()
    finally:
        db.close()


@celery_app.task
def send_new_message_notification(
    recipient_email: str, sender_name: str, listing_title: str
):
    subject = f"New message about {listing_title}"
    body = f"You have received a new message from {sender_name} about your listing '{listing_title}'. Please log in to Fresh Trade to view your messages."
    send_email_task.delay(recipient_email, subject, body)
