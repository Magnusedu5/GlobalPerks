import os
import logging
import resend

logger = logging.getLogger(__name__)
resend.api_key = os.environ.get('RESEND_API_KEY', '')


def _get_from_email():
    return os.environ.get('RESEND_FROM_EMAIL', 'bookings@globalperks.com')


def send_booking_confirmation(booking_data: dict) -> None:
    """Auto-reply to client. Never raises."""
    try:
        name = booking_data.get('name', '')
        email = booking_data.get('email', '')
        service = booking_data.get('service', '').title()
        date = booking_data.get('preferred_date', '')

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#0A0A0A;font-family:'Courier New',monospace;">
          <div style="max-width:600px;margin:0 auto;padding:40px 20px;">
            <div style="border-bottom:1px solid #2A2A2A;padding-bottom:24px;margin-bottom:32px;">
              <h1 style="color:#D9A640;font-family:Georgia,serif;font-size:28px;margin:0;font-weight:normal;">
                GlobalPerks
              </h1>
              <p style="color:#606058;font-size:11px;letter-spacing:0.1em;text-transform:uppercase;margin:4px 0 0;">
                Premium Photography
              </p>
            </div>
            <p style="color:#A0A09A;font-size:14px;line-height:1.7;margin:0 0 16px;">
              Hi {name},
            </p>
            <p style="color:#F5F5F0;font-size:16px;line-height:1.7;margin:0 0 24px;">
              Thank you for reaching out. Your booking request has been received and we're excited to hear from you.
            </p>
            <div style="background:#1A1A1A;border:1px solid #2A2A2A;border-left:3px solid #D9A640;padding:20px 24px;margin:0 0 32px;">
              <p style="color:#606058;font-size:11px;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 12px;">
                Your Request
              </p>
              <p style="color:#F5F5F0;font-size:14px;margin:0 0 8px;">
                <span style="color:#A0A09A;">Service:</span> {service}
              </p>
              <p style="color:#F5F5F0;font-size:14px;margin:0;">
                <span style="color:#A0A09A;">Preferred date:</span> {date}
              </p>
            </div>
            <p style="color:#A0A09A;font-size:14px;line-height:1.7;margin:0 0 32px;">
              We'll review your request and get back to you within <strong style="color:#F5F5F0;">24 hours</strong> to confirm availability and discuss the details.
            </p>
            <p style="color:#606058;font-size:13px;line-height:1.7;margin:0;border-top:1px solid #2A2A2A;padding-top:24px;">
              GlobalPerks Photography<br>
              Lagos, Nigeria · Shooting Worldwide
            </p>
          </div>
        </body>
        </html>
        """

        resend.Emails.send({
            "from": _get_from_email(),
            "to": [email],
            "subject": "We received your booking request — GlobalPerks",
            "html": html_body,
        })
        logger.info(f"Confirmation email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {e}")


def send_booking_notification(booking_data: dict) -> None:
    """Alert to photographer. Never raises."""
    try:
        notification_email = os.environ.get('NOTIFICATION_EMAIL', '')
        if not notification_email:
            logger.warning("NOTIFICATION_EMAIL not set — skipping notification")
            return

        name = booking_data.get('name', '')
        email = booking_data.get('email', '')
        phone = booking_data.get('phone', '')
        service = booking_data.get('service', '').title()
        date = booking_data.get('preferred_date', '')
        message = booking_data.get('message', 'No message provided')
        booking_id = booking_data.get('id', '')

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#0A0A0A;font-family:'Courier New',monospace;">
          <div style="max-width:600px;margin:0 auto;padding:40px 20px;">
            <div style="background:#1A1A1A;border:1px solid #2A2A2A;border-top:3px solid #D9A640;padding:24px;">
              <p style="color:#606058;font-size:11px;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 16px;">
                New Booking Request
              </p>
              <table style="width:100%;border-collapse:collapse;">
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;width:40%;">Name</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">{name}</td></tr>
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">Email</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;"><a href="mailto:{email}" style="color:#D9A640;">{email}</a></td></tr>
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">Phone</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">{phone}</td></tr>
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">Service</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">{service}</td></tr>
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">Preferred date</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;border-bottom:1px solid #2A2A2A;">{date}</td></tr>
                <tr><td style="color:#A0A09A;font-size:13px;padding:8px 0;" valign="top">Message</td><td style="color:#F5F5F0;font-size:13px;padding:8px 0;">{message}</td></tr>
              </table>
              <div style="margin-top:24px;">
                <a href="{os.environ.get('BACKEND_URL', 'http://localhost:8000')}/admin-panel/bookings/{booking_id}/"
                   style="background:#D9A640;color:#0A0A0A;padding:10px 20px;text-decoration:none;font-size:13px;font-weight:500;display:inline-block;">
                  View in Admin &rarr;
                </a>
              </div>
            </div>
          </div>
        </body>
        </html>
        """

        resend.Emails.send({
            "from": _get_from_email(),
            "to": [notification_email],
            "subject": f"New booking request — {name} ({service})",
            "html": html_body,
        })
        logger.info(f"Notification email sent for booking {booking_id}")
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")
