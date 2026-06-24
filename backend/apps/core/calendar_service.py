import os
import json
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def create_calendar_event(booking: dict):
    """
    Creates a Google Calendar event for a confirmed booking.
    Returns the event ID on success, None on any failure. Never raises.
    """
    try:
        service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '')
        calendar_id = os.environ.get('GOOGLE_CALENDAR_ID', '')

        if not service_account_json or not calendar_id:
            logger.warning("Google Calendar env vars not configured — skipping")
            return None

        service_account_info = json.loads(service_account_json)

        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/calendar']
        )

        service = build('calendar', 'v3', credentials=credentials)

        name = booking.get('name', '')
        service_type = booking.get('service', '').title()
        date = booking.get('preferred_date', '')

        event = {
            'summary': f"{service_type} — {name}",
            'description': (
                f"Client: {name}\n"
                f"Email: {booking.get('email', '')}\n"
                f"Phone: {booking.get('phone', '')}\n"
                f"Message: {booking.get('message', '')}"
            ),
            'start': {
                'dateTime': f"{date}T09:00:00",
                'timeZone': 'Africa/Lagos',
            },
            'end': {
                'dateTime': f"{date}T11:00:00",
                'timeZone': 'Africa/Lagos',
            },
            'attendees': [
                {'email': booking.get('email', '')}
            ],
            'sendUpdates': 'all',
        }

        created_event = service.events().insert(
            calendarId=calendar_id,
            body=event,
            sendUpdates='all'
        ).execute()

        event_id = created_event.get('id')
        logger.info(f"Calendar event created: {event_id} for booking {booking.get('id')}")
        return event_id

    except Exception as e:
        logger.error(f"Google Calendar event creation failed: {e}", exc_info=True)
        return None
