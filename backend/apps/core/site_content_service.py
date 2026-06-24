import logging
from apps.core.turso import get_connection

logger = logging.getLogger(__name__)

SECTION_ORDER = [
    'global', 'hero', 'featured_work', 'about_teaser',
    'services_overview', 'testimonials', 'cta',
    'portfolio', 'services_page', 'about_page', 'contact_page',
]

SECTION_LABELS = {
    'global':            'Global (nav, footer)',
    'hero':              'Homepage — Hero',
    'featured_work':     'Homepage — Featured Work photos',
    'about_teaser':      'Homepage — About teaser',
    'services_overview': 'Homepage — Services cards',
    'testimonials':      'Homepage — Testimonials',
    'cta':               'Homepage — CTA band',
    'portfolio':         'Portfolio page',
    'services_page':     'Services page',
    'about_page':        'About page',
    'contact_page':      'Contact page',
}


class SiteContentService:

    def _row_to_dict(self, cursor, row):
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))

    def get_all_as_dict(self) -> dict:
        conn = get_connection()
        cursor = conn.execute("SELECT key, value FROM site_content")
        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}

    def get_all_grouped(self) -> dict:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT key, value, type, label, section FROM site_content ORDER BY id ASC"
        )
        rows = cursor.fetchall()
        grouped = {s: [] for s in SECTION_ORDER}
        grouped['_other'] = []
        for row in rows:
            item = self._row_to_dict(cursor, row)
            section = item['section']
            if section in grouped:
                grouped[section].append(item)
            else:
                grouped['_other'].append(item)
        return grouped

    def update_text(self, key: str, value: str) -> bool:
        try:
            conn = get_connection()
            conn.execute("""
                UPDATE site_content
                SET value = ?, updated_at = datetime('now')
                WHERE key = ? AND type = 'text'
            """, (value.strip(), key))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update content key '{key}': {e}")
            return False

    def update_image(self, key: str, filepath: str) -> bool:
        try:
            conn = get_connection()
            conn.execute("""
                UPDATE site_content
                SET value = ?, updated_at = datetime('now')
                WHERE key = ? AND type = 'image'
            """, (filepath, key))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update image key '{key}': {e}")
            return False

    def bulk_update_text(self, updates: dict) -> int:
        count = 0
        for key, value in updates.items():
            if self.update_text(key, value):
                count += 1
        return count

    def get_section_keys(self, section: str) -> list:
        conn = get_connection()
        cursor = conn.execute(
            "SELECT key, value, type, label FROM site_content WHERE section = ? ORDER BY id",
            (section,)
        )
        rows = cursor.fetchall()
        return [self._row_to_dict(cursor, r) for r in rows]
