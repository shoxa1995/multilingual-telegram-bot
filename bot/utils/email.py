"""
Email notification utilities for the booking system.
Used for sending refund notifications and other important updates.
"""
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Initialize logger
logger = logging.getLogger(__name__)

# Email settings
EMAIL_ENABLED = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
EMAIL_FROM = os.environ.get('EMAIL_FROM', 'noreply@example.com')

# Set up Jinja2 environment for email templates
template_env = Environment(loader=FileSystemLoader('./templates/email'))


def format_currency(amount):
    """Format an amount in smallest currency unit to a readable format."""
    if amount is None:
        return "0.00"
    
    # Convert from smallest unit to main unit (e.g., tiyin to som)
    amount_decimal = amount / 100.0
    
    # Format with comma as thousand separator and 2 decimal places
    return f"{amount_decimal:,.2f}"


def render_template(template_name, **context):
    """Render a template with the given context variables."""
    template = template_env.get_template(template_name)
    return template.render(**context)


def send_email(to_email, subject, html_content, cc=None, bcc=None):
    """
    Send an email with the given parameters.
    
    Args:
        to_email: Recipient email address (can be comma-separated for multiple recipients)
        subject: Email subject
        html_content: HTML content of the email
        cc: Carbon copy recipients (optional)
        bcc: Blind carbon copy recipients (optional)
        
    Returns:
        Boolean indicating success or failure
    """
    if not EMAIL_ENABLED:
        logger.info("Email sending is disabled. Would have sent email to: %s", to_email)
        return True
        
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured. Cannot send email.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_FROM
        msg['To'] = to_email
        
        if cc:
            msg['Cc'] = cc
        if bcc:
            msg['Bcc'] = bcc
            
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            
            # Get all recipients
            all_recipients = []
            if to_email:
                all_recipients.extend(to_email.split(','))
            if cc:
                all_recipients.extend(cc.split(','))
            if bcc:
                all_recipients.extend(bcc.split(','))
                
            server.sendmail(EMAIL_FROM, all_recipients, msg.as_string())
            
        logger.info("Email sent successfully to: %s", to_email)
        return True
    except Exception as e:
        logger.exception("Error sending email: %s", str(e))
        return False


def send_refund_notification(booking, user_email=None):
    """
    Send a refund notification email for a booking.
    
    Args:
        booking: The booking object
        user_email: Optional email address (if not available in user profile)
        
    Returns:
        Boolean indicating success or failure
    """
    try:
        # Get user email from profile or use provided email
        to_email = user_email
        if not to_email and hasattr(booking.user, 'email'):
            to_email = booking.user.email
            
        if not to_email:
            logger.warning("No email address available for user ID: %s", booking.user_id)
            return False
            
        # Prepare context data for template
        context = {
            'user_name': f"{booking.user.first_name} {booking.user.last_name or ''}".strip(),
            'booking_id': booking.id,
            'staff_name': booking.staff.name,
            'booking_date': booking.booking_date.strftime('%d %B %Y, %H:%M'),
            'duration': booking.duration_minutes,
            'amount': format_currency(booking.price),
            'refund_date': datetime.now().strftime('%d %B %Y, %H:%M')
        }
        
        # Render email template
        html_content = render_template('refund_notification.html', **context)
        
        # Send the email
        subject = f"Refund Processed for Booking #{booking.id}"
        return send_email(to_email, subject, html_content)
    except Exception as e:
        logger.exception("Error sending refund notification: %s", str(e))
        return False