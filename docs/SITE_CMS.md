# GlobalPerks — Site CMS (Media Manager + Content Editor)

Read this entire file before writing any code. This adds a complete Content Management
System to the already-built GlobalPerks project. Perfecta can log into her admin
dashboard and update every image and every piece of text on the public website without
touching any code.

Architecture: Hybrid. Content and image paths live in Turso. A single endpoint
`GET /api/site-content/` returns all content as JSON. Each frontend HTML page runs
a small JS snippet on load that fetches this JSON and fills in text and image src
values using data attributes. Pages fall back to default hardcoded values if the
API is unavailable (offline-safe).

Do not modify any existing files unless explicitly instructed.

---

## How It Works (read this before coding)

### Content keys
Every editable element on the website has a unique string key, e.g.:
- `hero_headline` → the hero section headline
- `hero_subtext` → the hero subtitle
- `about_bio_1` → first paragraph of about section
- `service_portraits_title` → service card title
- `hero_image` → hero background image path
- `portfolio_photo_1` → first portfolio grid photo

### Database storage
One Turso table: `site_content`
Each row: `key` (unique), `value` (the text or image URL), `type` (`text` or `image`),
`label` (human-readable label for the admin form), `section` (groups fields in admin UI),
`updated_at`.

### Public API
`GET /api/site-content/` returns all rows as a flat JSON object:
```json
{
  "hero_headline": "Moments That Live Forever",
  "hero_subtext": "Capturing beauty in moments.",
  "hero_image": "/media/site/hero.jpg",
  ...
}
```
No authentication. Cached in browser for 5 minutes via Cache-Control header.

### Frontend injection
Every HTML page includes one shared script block at the bottom that:
1. Fetches `/api/site-content/` (with a 3s timeout)
2. Loops over all elements with `data-content="key"` and sets their innerHTML
3. Loops over all elements with `data-src="key"` and sets their `src` or
   `background-image` CSS
4. If fetch fails or times out, silently does nothing (default HTML shows)

### Admin CMS panel
A new section in the admin dashboard where Perfecta sees every editable field
grouped by page section. Text fields are `<textarea>` or `<input>`. Image fields
show the current image preview + an upload button. Saving sends a POST request
that updates the Turso row and (for images) saves the file to `/media/site/`.

---

## STEP 1 — Database: site_content table

In `backend/apps/core/turso.py`, add this CREATE TABLE inside `init_db()` after
the existing tables:

```sql
CREATE TABLE IF NOT EXISTS site_content (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    key        TEXT NOT NULL UNIQUE,
    value      TEXT NOT NULL DEFAULT '',
    type       TEXT NOT NULL DEFAULT 'text',
    label      TEXT NOT NULL DEFAULT '',
    section    TEXT NOT NULL DEFAULT 'general',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

Then add a new function `seed_site_content()` in `turso.py` that inserts default
rows using INSERT OR IGNORE (so it never overwrites existing values):

```python
def seed_site_content():
    """
    Inserts default content rows. Uses INSERT OR IGNORE so existing
    customised values are never overwritten. Safe to run repeatedly.
    """
    conn = get_connection()
    defaults = [
        # (key, value, type, label, section)

        # --- GLOBAL ---
        ('nav_cta_text',        'Book a Session',              'text',  'Nav CTA button text',        'global'),
        ('footer_tagline',      'Capturing beauty in moments.','text',  'Footer tagline',             'global'),
        ('footer_location',     'Calabar, Nigeria · Travel-Ready','text','Footer location line',      'global'),
        ('footer_instagram',    'https://instagram.com/globalperks_','text','Instagram URL',           'global'),
        ('footer_instagram_weddings','https://instagram.com/globalperks_lovestories','text','Wedding Instagram URL','global'),

        # --- HOMEPAGE HERO ---
        ('hero_eyebrow',        'PORTRAIT · FASHION · FAMILY · CALABAR','text','Hero eyebrow label',   'hero'),
        ('hero_headline_line1', 'Moments That',                'text',  'Hero headline line 1',       'hero'),
        ('hero_headline_line2', 'Live Forever',                'text',  'Hero headline line 2 (italic)','hero'),
        ('hero_subtext',        'Capturing beauty in moments — one frame at a time.','text','Hero subtext','hero'),
        ('hero_cta_primary',    'View Portfolio',              'text',  'Hero primary button text',   'hero'),
        ('hero_cta_secondary',  'Book a Session',              'text',  'Hero secondary button text', 'hero'),
        ('hero_image',          '',                            'image', 'Hero background image',      'hero'),

        # --- FEATURED WORK ---
        ('work_section_label',  'SELECTED WORK',               'text',  'Section label',              'featured_work'),
        ('work_section_heading','Stories Worth Telling',       'text',  'Section heading',            'featured_work'),
        ('work_photo_1',        '',                            'image', 'Featured photo 1',           'featured_work'),
        ('work_photo_2',        '',                            'image', 'Featured photo 2',           'featured_work'),
        ('work_photo_3',        '',                            'image', 'Featured photo 3',           'featured_work'),
        ('work_photo_4',        '',                            'image', 'Featured photo 4',           'featured_work'),
        ('work_photo_5',        '',                            'image', 'Featured photo 5',           'featured_work'),
        ('work_photo_6',        '',                            'image', 'Featured photo 6',           'featured_work'),

        # --- ABOUT TEASER (homepage) ---
        ('about_teaser_label',  'ABOUT PERFECTA',              'text',  'Section label',              'about_teaser'),
        ('about_teaser_heading','People Saw Beauty in What I Captured','text','Section heading',       'about_teaser'),
        ('about_teaser_bio',    'GlobalPerks started with one simple thing — a camera and an eye for what others walked past. Today, Perfecta shoots portraits, headshots, maternity, family, and brand sessions from her Calabar studio, travelling wherever the story takes her.','text','Teaser bio text','about_teaser'),
        ('about_teaser_stat1_number','295+',                   'text',  'Stat 1 number',              'about_teaser'),
        ('about_teaser_stat1_label', 'Sessions',               'text',  'Stat 1 label',               'about_teaser'),
        ('about_teaser_stat2_number','5+',                     'text',  'Stat 2 number',              'about_teaser'),
        ('about_teaser_stat2_label', 'Years',                  'text',  'Stat 2 label',               'about_teaser'),
        ('about_teaser_stat3_number','Travel-Ready',           'text',  'Stat 3 number',              'about_teaser'),
        ('about_teaser_stat3_label', 'Nationwide',             'text',  'Stat 3 label',               'about_teaser'),
        ('about_teaser_image',  '',                            'image', 'About teaser photo',         'about_teaser'),

        # --- SERVICES OVERVIEW (homepage cards) ---
        ('service_1_title',     'Portraits',                   'text',  'Service 1 title',            'services_overview'),
        ('service_1_desc',      'Personal portrait sessions that celebrate who you are.','text','Service 1 description','services_overview'),
        ('service_1_price',     'From ₦50,000',                'text',  'Service 1 price',            'services_overview'),
        ('service_2_title',     'Headshots',                   'text',  'Service 2 title',            'services_overview'),
        ('service_2_desc',      'Professional headshots for corporate teams and personal brands.','text','Service 2 description','services_overview'),
        ('service_2_price',     'From ₦35,000',                'text',  'Service 2 price',            'services_overview'),
        ('service_3_title',     'Maternity & Family',          'text',  'Service 3 title',            'services_overview'),
        ('service_3_desc',      'Tender sessions capturing new life and the people you love most.','text','Service 3 description','services_overview'),
        ('service_3_price',     'From ₦60,000',                'text',  'Service 3 price',            'services_overview'),
        ('service_4_title',     'Events',                      'text',  'Service 4 title',            'services_overview'),
        ('service_4_desc',      'Every milestone documented with speed and precision.','text','Service 4 description','services_overview'),
        ('service_4_price',     'From ₦80,000',                'text',  'Service 4 price',            'services_overview'),
        ('service_5_title',     'Brand & Commercial',          'text',  'Service 5 title',            'services_overview'),
        ('service_5_desc',      'Campaign shoots and branded content that stops the scroll.','text','Service 5 description','services_overview'),
        ('service_5_price',     'From ₦150,000',               'text',  'Service 5 price',            'services_overview'),

        # --- TESTIMONIALS ---
        ('testimonial_1_quote', 'Perfecta made me feel so comfortable. The photos came out beyond what I imagined.','text','Testimonial 1 quote','testimonials'),
        ('testimonial_1_name',  'Adaeze O.',                   'text',  'Testimonial 1 name',         'testimonials'),
        ('testimonial_1_type',  'Portrait session',            'text',  'Testimonial 1 shoot type',   'testimonials'),
        ('testimonial_2_quote', 'Professional, creative, and so easy to work with. Highly recommend.','text','Testimonial 2 quote','testimonials'),
        ('testimonial_2_name',  'Chidi M.',                    'text',  'Testimonial 2 name',         'testimonials'),
        ('testimonial_2_type',  'Corporate headshots',         'text',  'Testimonial 2 shoot type',   'testimonials'),
        ('testimonial_3_quote', 'Our maternity photos are absolutely stunning. We treasure every single one.','text','Testimonial 3 quote','testimonials'),
        ('testimonial_3_name',  'Ngozi & Emeka',               'text',  'Testimonial 3 name',         'testimonials'),
        ('testimonial_3_type',  'Maternity session',           'text',  'Testimonial 3 shoot type',   'testimonials'),

        # --- CTA BAND ---
        ('cta_headline',        "Let's Create Something Beautiful",'text','CTA band headline',        'cta'),
        ('cta_subtext',         'Book a session and let Perfecta tell your story.','text','CTA subtext','cta'),
        ('cta_button_text',     'Book a Session',              'text',  'CTA button text',            'cta'),

        # --- PORTFOLIO PAGE ---
        ('portfolio_heading',   'The Work',                    'text',  'Portfolio page heading',     'portfolio'),
        ('portfolio_subtext',   'A collection of moments, moods, and milestones.','text','Portfolio subtext','portfolio'),
        ('portfolio_photo_1',   '',  'image','Portfolio photo 1',  'portfolio'),
        ('portfolio_photo_2',   '',  'image','Portfolio photo 2',  'portfolio'),
        ('portfolio_photo_3',   '',  'image','Portfolio photo 3',  'portfolio'),
        ('portfolio_photo_4',   '',  'image','Portfolio photo 4',  'portfolio'),
        ('portfolio_photo_5',   '',  'image','Portfolio photo 5',  'portfolio'),
        ('portfolio_photo_6',   '',  'image','Portfolio photo 6',  'portfolio'),
        ('portfolio_photo_7',   '',  'image','Portfolio photo 7',  'portfolio'),
        ('portfolio_photo_8',   '',  'image','Portfolio photo 8',  'portfolio'),
        ('portfolio_photo_9',   '',  'image','Portfolio photo 9',  'portfolio'),
        ('portfolio_photo_10',  '',  'image','Portfolio photo 10', 'portfolio'),
        ('portfolio_photo_11',  '',  'image','Portfolio photo 11', 'portfolio'),
        ('portfolio_photo_12',  '',  'image','Portfolio photo 12', 'portfolio'),
        ('portfolio_cat_1',     'portraits','text','Portfolio photo 1 category (portraits/headshots/maternity/events/brand)','portfolio'),
        ('portfolio_cat_2',     'portraits','text','Portfolio photo 2 category','portfolio'),
        ('portfolio_cat_3',     'headshots','text','Portfolio photo 3 category','portfolio'),
        ('portfolio_cat_4',     'headshots','text','Portfolio photo 4 category','portfolio'),
        ('portfolio_cat_5',     'maternity','text','Portfolio photo 5 category','portfolio'),
        ('portfolio_cat_6',     'maternity','text','Portfolio photo 6 category','portfolio'),
        ('portfolio_cat_7',     'events',   'text','Portfolio photo 7 category','portfolio'),
        ('portfolio_cat_8',     'events',   'text','Portfolio photo 8 category','portfolio'),
        ('portfolio_cat_9',     'brand',    'text','Portfolio photo 9 category','portfolio'),
        ('portfolio_cat_10',    'brand',    'text','Portfolio photo 10 category','portfolio'),
        ('portfolio_cat_11',    'portraits','text','Portfolio photo 11 category','portfolio'),
        ('portfolio_cat_12',    'events',   'text','Portfolio photo 12 category','portfolio'),

        # --- SERVICES PAGE ---
        ('services_heading',    'Services & Investment',       'text',  'Services page heading',      'services_page'),
        ('service_detail_1_heading',    'Portraits',           'text',  'Service 1 full heading',     'services_page'),
        ('service_detail_1_desc',       'Every person carries a story worth telling. Perfecta\'s portrait sessions are relaxed, directed, and focused on one thing — showing you at your most confident and authentic.','text','Service 1 full description','services_page'),
        ('service_detail_1_includes',   'Full edited gallery · Digital files in high resolution · 1–2 hour session · Wardrobe consultation','text','Service 1 includes (· separated)','services_page'),
        ('service_detail_1_price',      'From ₦50,000',        'text',  'Service 1 price',            'services_page'),
        ('service_detail_1_image',      '',                    'image', 'Service 1 photo',            'services_page'),
        ('service_detail_2_heading',    'Headshots & Corporate','text', 'Service 2 full heading',     'services_page'),
        ('service_detail_2_desc',       'First impressions live online now. Whether you\'re a doctor, lawyer, executive, or entrepreneur — a sharp professional headshot tells people you take your work seriously.','text','Service 2 full description','services_page'),
        ('service_detail_2_includes',   'Individual or team sessions · LinkedIn and press-ready files · Same-week delivery · Studio or on-location','text','Service 2 includes','services_page'),
        ('service_detail_2_price',      'From ₦35,000',        'text',  'Service 2 price',            'services_page'),
        ('service_detail_2_image',      '',                    'image', 'Service 2 photo',            'services_page'),
        ('service_detail_3_heading',    'Maternity & Family',  'text',  'Service 3 full heading',     'services_page'),
        ('service_detail_3_desc',       'These are the moments you\'ll want to remember exactly as they felt. Warm, unhurried sessions that document new life, growing families, and the people who matter most.','text','Service 3 full description','services_page'),
        ('service_detail_3_includes',   'Bump and newborn sessions available · Full edited gallery · Print-ready files · Studio or outdoor','text','Service 3 includes','services_page'),
        ('service_detail_3_price',      'From ₦60,000',        'text',  'Service 3 price',            'services_page'),
        ('service_detail_3_image',      '',                    'image', 'Service 3 photo',            'services_page'),
        ('service_detail_4_heading',    'Events',              'text',  'Service 4 full heading',     'services_page'),
        ('service_detail_4_desc',       'Nursing inductions, graduation ceremonies, brand launches, award nights — Perfecta captures the energy and emotion of every milestone with speed and precision.','text','Service 4 full description','services_page'),
        ('service_detail_4_includes',   'Full event coverage · Fast turnaround · Crowd and detail shots · Candid and directed moments','text','Service 4 includes','services_page'),
        ('service_detail_4_price',      'From ₦80,000',        'text',  'Service 4 price',            'services_page'),
        ('service_detail_4_image',      '',                    'image', 'Service 4 photo',            'services_page'),
        ('service_detail_5_heading',    'Brand & Commercial',  'text',  'Service 5 full heading',     'services_page'),
        ('service_detail_5_desc',       'Your brand deserves imagery that matches its quality. From fashion lookbooks to product campaigns, Perfecta creates content that stops the scroll and sells the vision.','text','Service 5 full description','services_page'),
        ('service_detail_5_includes',   'Creative direction · Full licensed files · Multiple looks · Collaboration with brands and stylists','text','Service 5 includes','services_page'),
        ('service_detail_5_price',      'From ₦150,000',       'text',  'Service 5 price',            'services_page'),
        ('service_detail_5_image',      '',                    'image', 'Service 5 photo',            'services_page'),

        # --- ABOUT PAGE ---
        ('about_heading',       'Behind the Lens',             'text',  'About page heading',         'about_page'),
        ('about_pull_quote',    'GlobalPerks started with one simple thing... people saw beauty in what I captured.','text','Pull quote (italic, gold border)','about_page'),
        ('about_bio_1',         'Before GlobalPerks had a name, it had a feeling. Perfecta picked up a camera not because she planned a career, but because people kept stopping to ask about the photos she was taking. What started as curiosity became a calling.','text','Bio paragraph 1','about_page'),
        ('about_bio_2',         'Based in Calabar and available to travel anywhere the story leads, Perfecta has spent five years building a body of work that spans personal portraits, corporate headshots, maternity sessions, brand campaigns, and live events. Her clients range from fresh graduates marking a milestone to established brands building their visual identity.','text','Bio paragraph 2','about_page'),
        ('about_bio_3',         'Her approach is simple: make people feel comfortable, then capture them when they forget she\'s there. The result is images that feel both polished and real — because they are.','text','Bio paragraph 3','about_page'),
        ('about_main_image',    '',                            'image', 'About page main photo',      'about_page'),
        ('about_secondary_image','',                           'image', 'About page secondary photo', 'about_page'),
        ('about_value_1_title', 'LIGHT',                       'text',  'Value 1 title',              'about_page'),
        ('about_value_1_desc',  'Every session is built around beautiful, flattering light.','text','Value 1 description','about_page'),
        ('about_value_2_title', 'PEOPLE',                      'text',  'Value 2 title',              'about_page'),
        ('about_value_2_desc',  'She photographs people, not poses — the real moments land hardest.','text','Value 2 description','about_page'),
        ('about_value_3_title', 'STORY',                       'text',  'Value 3 title',              'about_page'),
        ('about_value_3_desc',  'Each image is a frame in something larger — your story.','text','Value 3 description','about_page'),

        # --- CONTACT PAGE ---
        ('contact_heading',     'Get in Touch',                'text',  'Contact page heading',       'contact_page'),
        ('contact_subheading',  "Let's Work Together",         'text',  'Contact section subheading', 'contact_page'),
        ('contact_email',       'hello@globalperks.com',       'text',  'Contact email address',      'contact_page'),
        ('contact_phone',       '',                            'text',  'Phone number (optional)',     'contact_page'),
        ('contact_response_time','All enquiries answered within 24 hours.','text','Response time note','contact_page'),
        ('contact_location',    'Based in Calabar · Available for travel nationwide & beyond','text','Location note','contact_page'),
    ]

    for key, value, ctype, label, section in defaults:
        conn.execute("""
            INSERT OR IGNORE INTO site_content (key, value, type, label, section)
            VALUES (?, ?, ?, ?, ?)
        """, (key, value, ctype, label, section))
    conn.commit()
    logger.info(f"Site content seeded — {len(defaults)} keys")
```

Update `scripts/init_db.py` to also call `seed_site_content()`:

```python
from apps.core.turso import init_db, seed_site_content
init_db()
seed_site_content()
print("Database tables created and site content seeded.")
```

---

## STEP 2 — Site Content Service

Create `backend/apps/core/site_content_service.py`:

```python
import os
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
        """Returns {key: value} flat dict — used by the public API."""
        conn = get_connection()
        cursor = conn.execute("SELECT key, value FROM site_content")
        rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}

    def get_all_grouped(self) -> dict:
        """
        Returns content grouped by section for the admin UI.
        {section: [{'key','value','type','label','section'}, ...]}
        """
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
        """Updates a text content key. Returns True on success."""
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
        """Updates an image content key with a relative media path."""
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
        """
        Updates multiple text keys at once.
        updates = {key: value, ...}
        Returns count of successful updates.
        """
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
```

---

## STEP 3 — Public API Endpoint

In `backend/apps/bookings/urls.py`, add a new URL pattern:

```python
from .views import BookingCreateView, SiteContentView

urlpatterns = [
    path('bookings/', BookingCreateView.as_view(), name='booking-create'),
    path('site-content/', SiteContentView.as_view(), name='site-content'),
]
```

In `backend/apps/bookings/views.py`, add this new view:

```python
from apps.core.site_content_service import SiteContentService
from django.views.decorators.cache import cache_control
from django.utils.decorators import method_decorator

@method_decorator(cache_control(max_age=300, public=True), name='dispatch')
class SiteContentView(APIView):
    """
    GET /api/site-content/
    Returns all site content as a flat JSON object.
    Cached 5 minutes. No authentication required.
    """
    def get(self, request):
        try:
            content = SiteContentService().get_all_as_dict()
            # Build absolute URLs for image values
            result = {}
            for key, value in content.items():
                if value and value.startswith('media/'):
                    result[key] = request.build_absolute_uri('/' + value)
                else:
                    result[key] = value
            return Response(result)
        except Exception as e:
            logger.error(f"Site content API error: {e}", exc_info=True)
            return Response({}, status=500)
```

---

## STEP 4 — Admin CMS Views

Add these views to `backend/apps/admin_panel/views.py`.

Add at the top of the file (with other imports):
```python
from apps.core.site_content_service import SiteContentService, SECTION_LABELS, SECTION_ORDER
```

Add these two view functions:

```python
@admin_required
def cms_view(request):
    """
    GET  — renders the full CMS editor
    POST — handles text field saves (section-by-section) OR image uploads
    """
    service = SiteContentService()

    if request.method == 'POST':
        action = request.POST.get('action', 'save_text')

        # --- Save text fields (one section at a time) ---
        if action == 'save_text':
            section = request.POST.get('section', '')
            section_keys = service.get_section_keys(section)
            text_keys = [k['key'] for k in section_keys if k['type'] == 'text']

            updates = {}
            for key in text_keys:
                if key in request.POST:
                    updates[key] = request.POST[key]

            count = service.bulk_update_text(updates)
            logger.info(f"CMS: saved {count} text fields in section '{section}'")
            return redirect(f'/admin-panel/cms/?saved={section}')

        # --- Upload image ---
        elif action == 'upload_image':
            key = request.POST.get('key', '')
            image_file = request.FILES.get('image')

            if not key or not image_file:
                return redirect('/admin-panel/cms/?error=missing_image')

            ext = os.path.splitext(image_file.name)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                return redirect('/admin-panel/cms/?error=invalid_type')

            # Save to /media/site/<key>.<ext>
            site_media_dir = os.path.join(settings.MEDIA_ROOT, 'site')
            os.makedirs(site_media_dir, exist_ok=True)

            # Remove old file if exists
            old_value = service.get_all_as_dict().get(key, '')
            if old_value:
                old_path = os.path.join(settings.MEDIA_ROOT, old_value.replace('media/', ''))
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception:
                        pass

            filename = f"{key}{ext}"
            filepath = os.path.join(site_media_dir, filename)
            with open(filepath, 'wb+') as dest:
                for chunk in image_file.chunks():
                    dest.write(chunk)

            relative_path = f"media/site/{filename}"
            service.update_image(key, relative_path)
            return redirect(f'/admin-panel/cms/?saved_image={key}')

    # GET
    grouped = service.get_all_grouped()
    saved_section = request.GET.get('saved', '')
    saved_image = request.GET.get('saved_image', '')
    error = request.GET.get('error', '')

    # Build image preview URLs
    base_url = request.build_absolute_uri('/')
    for section_items in grouped.values():
        for item in section_items:
            if item['type'] == 'image' and item['value']:
                item['preview_url'] = base_url + item['value']
            else:
                item['preview_url'] = ''

    return render(request, 'admin_panel/cms.html', {
        'grouped': grouped,
        'section_order': SECTION_ORDER,
        'section_labels': SECTION_LABELS,
        'saved_section': saved_section,
        'saved_image': saved_image,
        'error': error,
    })


@admin_required
def cms_delete_image_view(request, key):
    """POST — removes an image from a content key (sets it back to empty)."""
    if request.method == 'POST':
        service = SiteContentService()
        old_value = service.get_all_as_dict().get(key, '')
        if old_value:
            old_path = os.path.join(settings.MEDIA_ROOT, old_value.replace('media/', ''))
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass
        service.update_image(key, '')
    return redirect('/admin-panel/cms/?saved_image=removed')
```

Add to `backend/apps/admin_panel/urls.py`:

```python
path('cms/', views.cms_view, name='admin-cms'),
path('cms/delete-image/<str:key>/', views.cms_delete_image_view, name='admin-cms-delete-image'),
```

---

## STEP 5 — Admin CMS Template

Create `backend/apps/admin_panel/templates/admin_panel/cms.html`.
Extends `base.html`.

Add "Content" navigation link to `base.html` nav pointing to `/admin-panel/cms/`.

### CMS Template Structure

Page header: "Site Content" h1 + subtitle "Edit text and images on the public website"

Success banner (shown when ?saved= or ?saved_image= in URL, auto-dismiss after 3s):
- Green tinted: "Changes saved. The website will update within 5 minutes."

Error banner (shown when ?error= in URL):
- Red tinted: descriptive error message based on error code

Two-column layout (sidebar left 260px fixed, content right scrollable):

LEFT SIDEBAR — Section navigation:
A sticky vertical list of all sections as anchor links.
Each link: section label text, scrolls to that section's card.
Active section highlighted in gold when scrolled into view (IntersectionObserver JS).
Style: background var(--surface), border-right var(--border), full height,
padding 24px 16px, position sticky top 56px (below nav).

RIGHT CONTENT — Section cards:
For each section in SECTION_ORDER, render a card if the section has content:

Section card (.cms-section, id="{{ section_key }}", margin-bottom 32px):
- Section heading: SECTION_LABELS[section] — 11px, uppercase, letter-spaced, color var(--gold)
- Horizontal rule: var(--border), margin 12px 0 20px
- Form: POST to /admin-panel/cms/, enctype="multipart/form-data", {% csrf_token %}
  Hidden: <input type="hidden" name="action" value="save_text">
  Hidden: <input type="hidden" name="section" value="{{ section_key }}">

For each field in the section:

  IF type == 'text':
    Field wrapper (.cms-field, margin-bottom 20px):
    - Label: item.label — 11px, uppercase, letter-spaced, color var(--muted)
    - If value is longer than 80 chars: <textarea name="{{ item.key }}" rows="3">{{ item.value }}</textarea>
    - Else: <input type="text" name="{{ item.key }}" value="{{ item.value }}">
    - Both: full width, background var(--bg), border var(--border), color var(--text),
      font-family inherit, font-size 13px, padding 10px 12px, border-radius 2px,
      focus border-color var(--gold)

  IF type == 'image':
    Field wrapper (.cms-image-field, margin-bottom 24px):
    - Label: item.label — 11px, uppercase, letter-spaced, color var(--muted)
    - Current image preview (if item.preview_url exists):
      <img src="{{ item.preview_url }}" style="max-height:160px; max-width:280px;
      object-fit:cover; border:1px solid var(--border); border-radius:2px; display:block; margin-bottom:8px;">
    - If no preview: placeholder div (same dimensions, background var(--surface),
      border 1px dashed var(--border), display flex, align-items center,
      justify-content center, color var(--muted), font-size 12px)
      Text: "No image set"
    - Upload form (separate from the text save form — image uploads are individual):
      <form method="post" enctype="multipart/form-data" action="/admin-panel/cms/"
            style="display:inline-flex; gap:8px; align-items:center;">
        {% csrf_token %}
        <input type="hidden" name="action" value="upload_image">
        <input type="hidden" name="key" value="{{ item.key }}">
        <label class="upload-label">
          <input type="file" name="image" accept="image/jpeg,image/png,image/webp"
                 style="display:none" onchange="this.form.submit()">
          <span>{{ "Replace image" if item.preview_url else "Upload image" }}</span>
        </label>
      </form>
      If item.preview_url, also show remove form:
      <form method="post" action="/admin-panel/cms/delete-image/{{ item.key }}/"
            style="display:inline;">
        {% csrf_token %}
        <button type="submit" onclick="return confirm('Remove this image?')"
                style="background:none; border:none; color:var(--muted);
                font-size:12px; cursor:pointer; text-decoration:underline;">
          Remove
        </button>
      </form>

- Section save button (only for sections that have text fields):
  <button type="submit" class="cms-save-btn">Save [SECTION_LABELS[section]]</button>
  Style: background var(--gold), color #0A0604, border none, padding 10px 24px,
  font-family inherit, font-size 13px, font-weight 700, letter-spacing 0.05em,
  cursor pointer. Hover: background darkened.

Image upload labels (.upload-label):
  display inline-block, padding 8px 16px, border 1px solid var(--border),
  color var(--muted), font-size 12px, cursor pointer, border-radius 2px.
  Hover: border-color var(--gold), color var(--gold).

Sidebar active link JS (add at bottom of template):
```javascript
const sections = document.querySelectorAll('.cms-section');
const navLinks = document.querySelectorAll('.sidebar-link');
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinks.forEach(l => l.classList.remove('active'));
      const active = document.querySelector(`.sidebar-link[href="#${entry.target.id}"]`);
      if (active) active.classList.add('active');
    }
  });
}, { threshold: 0.2 });
sections.forEach(s => observer.observe(s));
```

Auto-dismiss success banner JS:
```javascript
const banner = document.querySelector('.success-banner');
if (banner) setTimeout(() => { banner.style.opacity = '0'; }, 3000);
```

---

## STEP 6 — Frontend JS Injection (add to ALL frontend HTML pages)

Add this shared content injection script to the bottom of every frontend HTML file,
just before the closing `</body>` tag. Replace `YOUR_BACKEND_URL` with the env-based
logic already used in `contact.html`.

This script goes in: `index.html`, `portfolio.html`, `services.html`,
`about.html`, `contact.html`.

```javascript
(function() {
  const BACKEND = window.location.hostname === 'localhost' ||
                  window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://your-backend.onrender.com'; // UPDATE BEFORE DEPLOY

  const CACHE_KEY = 'gp_site_content';
  const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  function applyContent(content) {
    // Text injection: <span data-content="hero_headline">Default</span>
    document.querySelectorAll('[data-content]').forEach(el => {
      const key = el.getAttribute('data-content');
      if (content[key] !== undefined && content[key] !== '') {
        el.innerHTML = content[key];
      }
    });

    // Image src injection: <img data-src="hero_image" src="placeholder.jpg">
    document.querySelectorAll('[data-src]').forEach(el => {
      const key = el.getAttribute('data-src');
      if (content[key] && content[key] !== '') {
        if (el.tagName === 'IMG') {
          el.src = content[key];
          el.removeAttribute('data-src');
        }
      }
    });

    // Background image injection: <div data-bg="hero_image">
    document.querySelectorAll('[data-bg]').forEach(el => {
      const key = el.getAttribute('data-bg');
      if (content[key] && content[key] !== '') {
        el.style.backgroundImage = `url('${content[key]}')`;
        el.removeAttribute('data-bg');
      }
    });

    // Portfolio category injection
    document.querySelectorAll('[data-cat]').forEach(el => {
      const key = el.getAttribute('data-cat');
      if (content[key] && content[key] !== '') {
        el.setAttribute('data-category', content[key]);
      }
    });
  }

  async function loadContent() {
    // Check cache first
    try {
      const cached = sessionStorage.getItem(CACHE_KEY);
      if (cached) {
        const { data, ts } = JSON.parse(cached);
        if (Date.now() - ts < CACHE_TTL) {
          applyContent(data);
          return;
        }
      }
    } catch(e) {}

    // Fetch from API with timeout
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000);
      const res = await fetch(`${BACKEND}/api/site-content/`, {
        signal: controller.signal
      });
      clearTimeout(timeout);
      if (!res.ok) return;
      const data = await res.json();
      applyContent(data);
      // Cache it
      try {
        sessionStorage.setItem(CACHE_KEY, JSON.stringify({ data, ts: Date.now() }));
      } catch(e) {}
    } catch(e) {
      // Silent fail — default HTML content shows
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadContent);
  } else {
    loadContent();
  }
})();
```

---

## STEP 7 — Add data attributes to all frontend HTML elements

Go through each frontend HTML file and add `data-content`, `data-src`, `data-bg`,
and `data-cat` attributes to every editable element. Do not remove existing
default text or src values — they serve as fallbacks when the API is unavailable.

### index.html — add these attributes:

Hero section:
- Eyebrow element: `data-content="hero_eyebrow"`
- Headline line 1: `data-content="hero_headline_line1"`
- Headline line 2 (the italic em): `data-content="hero_headline_line2"`
- Subtext paragraph: `data-content="hero_subtext"`
- Primary CTA button text: `data-content="hero_cta_primary"`
- Hero background container (div or section with background-image): `data-bg="hero_image"`

Featured work section:
- Section label: `data-content="work_section_label"`
- Section heading: `data-content="work_section_heading"`
- Each of the 6 gallery images: `data-src="work_photo_1"` through `data-src="work_photo_6"`

About teaser section:
- Section label: `data-content="about_teaser_label"`
- Heading: `data-content="about_teaser_heading"`
- Bio paragraph: `data-content="about_teaser_bio"`
- Stat 1 number: `data-content="about_teaser_stat1_number"`
- Stat 1 label: `data-content="about_teaser_stat1_label"`
- Stat 2 number: `data-content="about_teaser_stat2_number"`
- Stat 2 label: `data-content="about_teaser_stat2_label"`
- Stat 3 number: `data-content="about_teaser_stat3_number"`
- Stat 3 label: `data-content="about_teaser_stat3_label"`
- About teaser image: `data-src="about_teaser_image"`

Services overview cards (5 cards):
- Each title span: `data-content="service_1_title"` through `service_5_title`
- Each description: `data-content="service_1_desc"` through `service_5_desc`
- Each price: `data-content="service_1_price"` through `service_5_price`

Testimonials (3):
- Each quote: `data-content="testimonial_1_quote"` through `testimonial_3_quote`
- Each name: `data-content="testimonial_1_name"` through `testimonial_3_name`
- Each type: `data-content="testimonial_1_type"` through `testimonial_3_type`

CTA band:
- Headline: `data-content="cta_headline"`
- Subtext: `data-content="cta_subtext"`
- Button text: `data-content="cta_button_text"`

Footer (all pages share footer — add to each):
- Tagline: `data-content="footer_tagline"`
- Location: `data-content="footer_location"`

### portfolio.html — add these attributes:

- Page heading: `data-content="portfolio_heading"`
- Page subtext: `data-content="portfolio_subtext"`
- 12 gallery images: `data-src="portfolio_photo_1"` through `data-src="portfolio_photo_12"`
- 12 gallery items' category: `data-cat="portfolio_cat_1"` through `data-cat="portfolio_cat_12"`

### services.html — add these attributes:

- Page heading: `data-content="services_heading"`
- 5 service sections:
  Each: heading `data-content="service_detail_N_heading"`, desc `data-content="service_detail_N_desc"`,
  includes `data-content="service_detail_N_includes"`, price `data-content="service_detail_N_price"`,
  image `data-src="service_detail_N_image"` (N = 1 through 5)

### about.html — add these attributes:

- Page heading: `data-content="about_heading"`
- Pull quote: `data-content="about_pull_quote"`
- Bio paragraph 1: `data-content="about_bio_1"`
- Bio paragraph 2: `data-content="about_bio_2"`
- Bio paragraph 3: `data-content="about_bio_3"`
- Main photo: `data-src="about_main_image"`
- Secondary photo: `data-src="about_secondary_image"`
- Value 1 title: `data-content="about_value_1_title"`, desc: `data-content="about_value_1_desc"`
- Value 2 title: `data-content="about_value_2_title"`, desc: `data-content="about_value_2_desc"`
- Value 3 title: `data-content="about_value_3_title"`, desc: `data-content="about_value_3_desc"`

### contact.html — add these attributes:

- Page heading: `data-content="contact_heading"`
- Subheading: `data-content="contact_subheading"`
- Email display text: `data-content="contact_email"`
- Response time text: `data-content="contact_response_time"`
- Location text: `data-content="contact_location"`

---

## STEP 8 — Update init_db.py and run setup

Update `scripts/init_db.py` to import and call `seed_site_content`:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from apps.core.turso import init_db, seed_site_content
init_db()
seed_site_content()
print("Database tables created and site content seeded successfully.")
print("All default text content is now editable from /admin-panel/cms/")
```

---

## Verification Steps

```bash
# 1. Run init_db to create the new table and seed all content keys
python scripts/init_db.py
# → "Database tables created and site content seeded successfully."

# 2. Start the backend
python manage.py runserver

# 3. Test the public API
curl http://localhost:8000/api/site-content/
# → JSON object with ~80 keys including all text defaults and empty image keys

# 4. Log into admin
# Visit http://localhost:8000/admin-panel/cms/
# → CMS page loads with left sidebar (section nav) + right content (all fields)
# → Sidebar links scroll to sections
# → Edit a text field (e.g. hero_headline_line1), click Save
# → Success banner appears and dismisses after 3s
# → Re-open the page: the new value persists

# 5. Upload an image
# → Find "Hero background image" field in the Hero section
# → Click "Upload image", select a JPG
# → Page reloads with the image preview shown
# → Visit http://localhost:8000/media/site/hero_image.jpg — image accessible

# 6. Test frontend injection
# Open http://localhost:3000/index.html (via npx serve frontend -p 3000)
# → Page loads with default text first
# → Within 1–2 seconds, text updates to whatever was saved in CMS
# → If hero_image was uploaded, hero background updates to real photo
# → Open browser devtools → Network tab → confirm /api/site-content/ request made
# → Reload page → content loads from sessionStorage cache (no new API request)

# 7. Test offline fallback
# Stop the Django server
# Reload index.html → default hardcoded text shows (no errors, no blank content)
```

---

## How Perfecta Uses This

Once built, the workflow for Perfecta is:

1. Log into `/admin-panel/`
2. Click "Content" in the nav
3. Scroll to the section she wants to update (e.g. "Portfolio page")
4. For text: type new value → click Save
5. For photos: click "Upload image" next to the field → select photo from her phone or laptop
6. The public website updates within 5 minutes (sessionStorage cache expires)
7. For immediate update: open site in a new incognito window

She never needs to touch any code, ask a developer, or wait for a deployment.
