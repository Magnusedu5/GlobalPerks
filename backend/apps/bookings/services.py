import logging
from apps.core.turso import get_connection

logger = logging.getLogger(__name__)


class TursoBookingService:

    def create_booking(self, data: dict) -> dict:
        try:
            conn = get_connection()
            cursor = conn.execute(
                "INSERT INTO bookings (name, email, phone, service, preferred_date, message) VALUES (?, ?, ?, ?, ?, ?)",
                (data['name'], data['email'], data['phone'], data['service'], data['preferred_date'], data.get('message', ''))
            )
            conn.commit()
            row_id = cursor.lastrowid
            fetch_cursor = conn.execute("SELECT * FROM bookings WHERE id = ?", (row_id,))
            row = fetch_cursor.fetchone()
            return self._row_to_dict(fetch_cursor, row)
        except Exception as e:
            logger.error(f"create_booking failed: {e}", exc_info=True)
            raise

    def get_all_bookings(self, status_filter: str = None) -> list:
        try:
            conn = get_connection()
            if status_filter:
                cursor = conn.execute(
                    "SELECT * FROM bookings WHERE status = ? ORDER BY created_at DESC",
                    (status_filter,)
                )
            else:
                cursor = conn.execute("SELECT * FROM bookings ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_dict(cursor, row) for row in rows]
        except Exception as e:
            logger.error(f"get_all_bookings failed: {e}", exc_info=True)
            raise

    def get_booking_by_id(self, booking_id: int):
        try:
            conn = get_connection()
            cursor = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
            row = cursor.fetchone()
            if row is None:
                return None
            return self._row_to_dict(cursor, row)
        except Exception as e:
            logger.error(f"get_booking_by_id failed: {e}", exc_info=True)
            raise

    def update_booking_status(self, booking_id: int, new_status: str) -> dict:
        try:
            conn = get_connection()
            conn.execute(
                "UPDATE bookings SET status = ? WHERE id = ?",
                (new_status, booking_id)
            )
            conn.commit()
            cursor = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
            row = cursor.fetchone()
            return self._row_to_dict(cursor, row)
        except Exception as e:
            logger.error(f"update_booking_status failed: {e}", exc_info=True)
            raise

    def update_calendar_event_id(self, booking_id: int, event_id: str) -> None:
        try:
            conn = get_connection()
            conn.execute(
                "UPDATE bookings SET google_calendar_event_id = ? WHERE id = ?",
                (event_id, booking_id)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"update_calendar_event_id failed: {e}", exc_info=True)
            raise

    def get_stats(self) -> dict:
        try:
            conn = get_connection()
            total = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM bookings WHERE status = 'pending'").fetchone()[0]
            confirmed_this_month = conn.execute(
                "SELECT COUNT(*) FROM bookings WHERE status = 'confirmed' AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')"
            ).fetchone()[0]
            completed = conn.execute("SELECT COUNT(*) FROM bookings WHERE status = 'completed'").fetchone()[0]
            return {
                'total': total,
                'pending': pending,
                'confirmed_this_month': confirmed_this_month,
                'completed': completed,
            }
        except Exception as e:
            logger.error(f"get_stats failed: {e}", exc_info=True)
            raise

    def _row_to_dict(self, cursor, row) -> dict:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
