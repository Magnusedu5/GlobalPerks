import threading
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import BookingSerializer
from .services import TursoBookingService
from apps.core.site_content_service import SiteContentService

logger = logging.getLogger(__name__)


class BookingCreateView(APIView):
    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        try:
            data = dict(serializer.validated_data)
            data['preferred_date'] = str(data['preferred_date'])
            service = TursoBookingService()
            booking = service.create_booking(data)
            try:
                from apps.core.email_service import send_booking_confirmation, send_booking_notification
                threading.Thread(target=send_booking_confirmation, args=(booking,), daemon=True).start()
                threading.Thread(target=send_booking_notification, args=(booking,), daemon=True).start()
            except ImportError:
                pass
            return Response({'success': True, 'message': 'Booking received'}, status=201)
        except Exception as e:
            logger.error(f"Booking creation failed: {e}", exc_info=True)
            return Response({'error': 'Something went wrong. Please try again.'}, status=500)


class SiteContentView(APIView):
    def get(self, request):
        try:
            return Response(SiteContentService().get_all_as_dict())
        except Exception as e:
            logger.error(f"SiteContent fetch error: {e}", exc_info=True)
            return Response({}, status=200)
