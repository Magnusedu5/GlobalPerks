import os
import bcrypt
import logging
from apps.core.turso import get_connection

logger = logging.getLogger(__name__)


class TursoGalleryService:

    def _row_to_dict(self, cursor, row):
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    def create_album(self, data: dict) -> dict:
        conn = get_connection()
        password_hash = bcrypt.hashpw(
            data['password'].encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        conn.execute("""
            INSERT INTO albums
                (title, slug, client_name, client_email, password_hash,
                 description, shoot_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['title'],
            data['slug'],
            data['client_name'],
            data.get('client_email', ''),
            password_hash,
            data.get('description', ''),
            data.get('shoot_date', ''),
        ))
        conn.commit()
        cursor = conn.execute(
            "SELECT * FROM albums WHERE slug = ?", (data['slug'],)
        )
        return self._row_to_dict(cursor, cursor.fetchone())

    def get_all_albums(self) -> list:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT * FROM albums ORDER BY created_at DESC"
        )
        rows = cursor.fetchall()
        return [self._row_to_dict(cursor, r) for r in rows]

    def get_album_by_slug(self, slug: str) -> dict | None:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT * FROM albums WHERE slug = ?", (slug,)
        )
        row = cursor.fetchone()
        return self._row_to_dict(cursor, row) if row else None

    def get_album_by_id(self, album_id: int) -> dict | None:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT * FROM albums WHERE id = ?", (album_id,)
        )
        row = cursor.fetchone()
        return self._row_to_dict(cursor, row) if row else None

    def verify_password(self, slug: str, password: str) -> bool:
        album = self.get_album_by_slug(slug)
        if not album:
            return False
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                album['password_hash'].encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password check failed: {e}")
            return False

    def add_photo(self, album_id: int, filename: str, filepath: str,
                  caption: str = '', sort_order: int = 0) -> dict:
        conn = get_connection()
        conn.execute("""
            INSERT INTO album_photos
                (album_id, filename, filepath, caption, sort_order)
            VALUES (?, ?, ?, ?, ?)
        """, (album_id, filename, filepath, caption, sort_order))
        conn.commit()
        cursor = conn.execute(
            "SELECT * FROM album_photos WHERE album_id = ? ORDER BY sort_order",
            (album_id,)
        )
        rows = cursor.fetchall()
        return [self._row_to_dict(cursor, r) for r in rows]

    def get_photos(self, album_id: int) -> list:
        conn = get_connection()
        cursor = conn.execute("""
            SELECT * FROM album_photos
            WHERE album_id = ?
            ORDER BY sort_order ASC, created_at ASC
        """, (album_id,))
        rows = cursor.fetchall()
        return [self._row_to_dict(cursor, r) for r in rows]

    def delete_photo(self, photo_id: int) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM album_photos WHERE id = ?", (photo_id,))
        conn.commit()

    def set_cover(self, album_id: int, filepath: str) -> None:
        conn = get_connection()
        conn.execute(
            "UPDATE albums SET cover_photo = ? WHERE id = ?",
            (filepath, album_id)
        )
        conn.commit()

    def toggle_active(self, album_id: int) -> dict:
        conn = get_connection()
        album = self.get_album_by_id(album_id)
        new_state = 0 if album['is_active'] else 1
        conn.execute(
            "UPDATE albums SET is_active = ? WHERE id = ?",
            (new_state, album_id)
        )
        conn.commit()
        return self.get_album_by_id(album_id)

    def delete_album(self, album_id: int) -> None:
        conn = get_connection()
        conn.execute("DELETE FROM album_photos WHERE album_id = ?", (album_id,))
        conn.execute("DELETE FROM albums WHERE id = ?", (album_id,))
        conn.commit()

    def slug_exists(self, slug: str) -> bool:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT COUNT(*) FROM albums WHERE slug = ?", (slug,)
        )
        return cursor.fetchone()[0] > 0

    def get_photo_count(self, album_id: int) -> int:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT COUNT(*) FROM album_photos WHERE album_id = ?", (album_id,)
        )
        return cursor.fetchone()[0]
