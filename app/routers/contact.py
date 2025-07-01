from fastapi import APIRouter, Depends, HTTPException
from app.schemas import ContactForm
from app.tasks import send_email_task

router = APIRouter(prefix="/contact", tags=["contact"])


@router.post("/")
def send_contact_message(contact: ContactForm):
    try:
        # Send email to admin
        admin_subject = f"Contact Form: {contact.subject}"
        admin_body = f"""
        New contact form submission:
        
        Name: {contact.name}
        Email: {contact.email}
        Subject: {contact.subject}
        
        Message:
        {contact.message}
        """

        # Replace with actual admin email
        admin_email = "admin@freshtrade.com"
        send_email_task.delay(admin_email, admin_subject, admin_body)

        # Send confirmation to user
        user_subject = "Thank you for contacting Fresh Trade"
        user_body = f"""
        Dear {contact.name},
        
        Thank you for contacting Fresh Trade. We have received your message and will get back to you soon.
        
        Your message:
        Subject: {contact.subject}
        Message: {contact.message}
        
        Best regards,
        Fresh Trade Team
        """

        send_email_task.delay(contact.email, user_subject, user_body)

        return {"message": "Contact form submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send message")
