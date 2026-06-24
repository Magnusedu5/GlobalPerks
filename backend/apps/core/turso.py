import libsql
import os
import logging

logger = logging.getLogger(__name__)
_conn = None

def get_connection():
    global _conn
    if _conn is None:
        _conn = libsql.connect(
            database=os.environ['TURSO_DATABASE_URL'],
            auth_token=os.environ['TURSO_AUTH_TOKEN'],
        )
    return _conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            service TEXT NOT NULL,
            preferred_date TEXT NOT NULL,
            message TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            google_calendar_event_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS albums (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT NOT NULL,
            slug         TEXT NOT NULL UNIQUE,
            client_name  TEXT NOT NULL,
            client_email TEXT,
            password_hash TEXT NOT NULL,
            description  TEXT,
            shoot_date   TEXT,
            is_active    INTEGER NOT NULL DEFAULT 1,
            cover_photo  TEXT,
            created_at   TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS album_photos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            album_id   INTEGER NOT NULL,
            filename   TEXT NOT NULL,
            filepath   TEXT NOT NULL,
            caption    TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (album_id) REFERENCES albums(id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS site_content (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            key        TEXT NOT NULL UNIQUE,
            value      TEXT NOT NULL DEFAULT '',
            type       TEXT NOT NULL DEFAULT 'text',
            label      TEXT NOT NULL DEFAULT '',
            section    TEXT NOT NULL DEFAULT 'global',
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    logger.info("Turso tables initialised")


def seed_site_content():
    conn = get_connection()
    rows = [
        # key, value, type, label, section
        ('footer_tagline',           'Capturing beauty in moments.',                        'text',  'Footer tagline',               'global'),
        ('footer_location',          'Based in Calabar, Nigeria',                           'text',  'Footer location',              'global'),
        ('hero_eyebrow',             'Portrait · Fashion · Family · Calabar',               'text',  'Eyebrow label',                'hero'),
        ('hero_headline_line1',      'Moments That',                                        'text',  'Headline line 1',              'hero'),
        ('hero_headline_line2',      'Live Forever',                                        'text',  'Headline line 2 (italic)',     'hero'),
        ('hero_subtext',             'Portraits, weddings, and stories told with light.',   'text',  'Subtitle',                     'hero'),
        ('hero_cta_primary',         'View Portfolio',                                      'text',  'Primary CTA button',           'hero'),
        ('hero_image',               '',                                                    'image', 'Hero background photo',        'hero'),
        ('work_section_label',       'Selected Work',                                       'text',  'Section label',                'featured_work'),
        ('work_section_heading',     'Stories Worth Telling',                               'text',  'Section heading',              'featured_work'),
        ('work_photo_1',             '',                                                    'image', 'Featured photo 1',             'featured_work'),
        ('work_photo_2',             '',                                                    'image', 'Featured photo 2',             'featured_work'),
        ('work_photo_3',             '',                                                    'image', 'Featured photo 3 (tall)',      'featured_work'),
        ('about_teaser_label',       'About Perfecta',                                      'text',  'Eyebrow label',                'about_teaser'),
        ('about_teaser_heading',     'People Saw Beauty in What I Captured',                'text',  'Section heading',              'about_teaser'),
        ('about_teaser_bio',         'GlobalPerks started with one simple thing — a camera and an eye for what others walked past. Today, Perfecta shoots portraits, headshots, maternity, family, and brand sessions from her Calabar studio, travelling wherever the story takes her.', 'text', 'Bio paragraph', 'about_teaser'),
        ('about_teaser_stat1_number','295+',                                                'text',  'Stat 1 number',                'about_teaser'),
        ('about_teaser_stat1_label', 'Sessions',                                            'text',  'Stat 1 label',                 'about_teaser'),
        ('about_teaser_stat2_number','5+ Years',                                            'text',  'Stat 2 number',                'about_teaser'),
        ('about_teaser_stat2_label', 'Experience',                                          'text',  'Stat 2 label',                 'about_teaser'),
        ('about_teaser_stat3_number','Travel-Ready',                                        'text',  'Stat 3 number',                'about_teaser'),
        ('about_teaser_stat3_label', 'Available',                                           'text',  'Stat 3 label',                 'about_teaser'),
        ('about_teaser_image',       '',                                                    'image', 'About teaser photo',           'about_teaser'),
        ('service_1_title',          'Portraits',                                           'text',  'Service 1 name',               'services_overview'),
        ('service_1_desc',           'Personal portrait sessions that celebrate who you are — confident, natural, and beautifully lit.', 'text', 'Service 1 description', 'services_overview'),
        ('service_1_price',          'From ₦50,000',                                   'text',  'Service 1 price',              'services_overview'),
        ('service_2_title',          'Headshots',                                           'text',  'Service 2 name',               'services_overview'),
        ('service_2_desc',           'Professional headshots for corporate teams, doctors, lawyers, and personal brands.', 'text', 'Service 2 description', 'services_overview'),
        ('service_2_price',          'From ₦35,000',                                   'text',  'Service 2 price',              'services_overview'),
        ('service_3_title',          'Maternity & Family',                                  'text',  'Service 3 name',               'services_overview'),
        ('service_3_desc',           'Tender, warm sessions capturing new life and the people you love most.', 'text', 'Service 3 description', 'services_overview'),
        ('service_3_price',          'From ₦60,000',                                   'text',  'Service 3 price',              'services_overview'),
        ('service_4_title',          'Events',                                              'text',  'Service 4 name',               'services_overview'),
        ('service_4_desc',           'From inductions to launches — every milestone documented with intention.', 'text', 'Service 4 description', 'services_overview'),
        ('service_4_price',          'From ₦80,000',                                   'text',  'Service 4 price',              'services_overview'),
        ('service_5_title',          'Brand & Commercial',                                  'text',  'Service 5 name',               'services_overview'),
        ('service_5_desc',           'Branded content and campaign shoots for fashion, lifestyle, and product brands.', 'text', 'Service 5 description', 'services_overview'),
        ('service_5_price',          'From ₦150,000',                                  'text',  'Service 5 price',              'services_overview'),
        ('testimonial_1_quote',      'GlobalPerks captured everything we didn\'t know we needed. Every photo is a memory I\'ll treasure forever. The attention to light and emotion is extraordinary.', 'text', 'Testimonial 1 quote', 'testimonials'),
        ('testimonial_1_name',       'Adaeze & Chidi Okonkwo',                             'text',  'Testimonial 1 name',           'testimonials'),
        ('testimonial_1_type',       'Wedding · Lagos, 2024',                          'text',  'Testimonial 1 type',           'testimonials'),
        ('testimonial_2_quote',      'My brand has never looked this good. The commercial shoot exceeded every expectation — professional, creative, and fast to deliver. Absolute quality.', 'text', 'Testimonial 2 quote', 'testimonials'),
        ('testimonial_2_name',       'Tunde Fashola',                                       'text',  'Testimonial 2 name',           'testimonials'),
        ('testimonial_2_type',       'Commercial · Abuja, 2024',                       'text',  'Testimonial 2 type',           'testimonials'),
        ('testimonial_3_quote',      'I was nervous about portraits but GlobalPerks made it so natural. The results are stunning — I finally have photos I\'m proud to share.', 'text', 'Testimonial 3 quote', 'testimonials'),
        ('testimonial_3_name',       'Ngozi Eze',                                           'text',  'Testimonial 3 name',           'testimonials'),
        ('testimonial_3_type',       'Portraits · Port Harcourt, 2024',                'text',  'Testimonial 3 type',           'testimonials'),
        ('cta_headline',             "Let’s Create Something Beautiful",               'text',  'CTA headline',                 'cta'),
        ('cta_subtext',              'Every great photograph starts with a conversation.',  'text',  'CTA subtext',                  'cta'),
        ('cta_button_text',          'Book a Session',                                      'text',  'CTA button text',              'cta'),
        ('portfolio_heading',        'The Work',                                            'text',  'Page heading',                 'portfolio'),
        ('portfolio_subtext',        'A collection of moments, moods, and milestones',      'text',  'Page subtitle',                'portfolio'),
        ('portfolio_photo_1',        '',  'image', 'Portfolio photo 1',  'portfolio'),
        ('portfolio_photo_2',        '',  'image', 'Portfolio photo 2',  'portfolio'),
        ('portfolio_photo_3',        '',  'image', 'Portfolio photo 3',  'portfolio'),
        ('portfolio_photo_4',        '',  'image', 'Portfolio photo 4',  'portfolio'),
        ('portfolio_photo_5',        '',  'image', 'Portfolio photo 5',  'portfolio'),
        ('portfolio_photo_6',        '',  'image', 'Portfolio photo 6',  'portfolio'),
        ('portfolio_photo_7',        '',  'image', 'Portfolio photo 7',  'portfolio'),
        ('portfolio_photo_8',        '',  'image', 'Portfolio photo 8',  'portfolio'),
        ('portfolio_photo_9',        '',  'image', 'Portfolio photo 9',  'portfolio'),
        ('portfolio_photo_10',       '',  'image', 'Portfolio photo 10', 'portfolio'),
        ('portfolio_photo_11',       '',  'image', 'Portfolio photo 11', 'portfolio'),
        ('portfolio_photo_12',       '',  'image', 'Portfolio photo 12', 'portfolio'),
        ('portfolio_cat_1',          'portraits',   'text', 'Photo 1 category',  'portfolio'),
        ('portfolio_cat_2',          'wedding',     'text', 'Photo 2 category',  'portfolio'),
        ('portfolio_cat_3',          'commercial',  'text', 'Photo 3 category',  'portfolio'),
        ('portfolio_cat_4',          'events',      'text', 'Photo 4 category',  'portfolio'),
        ('portfolio_cat_5',          'travel',      'text', 'Photo 5 category',  'portfolio'),
        ('portfolio_cat_6',          'portraits',   'text', 'Photo 6 category',  'portfolio'),
        ('portfolio_cat_7',          'wedding',     'text', 'Photo 7 category',  'portfolio'),
        ('portfolio_cat_8',          'commercial',  'text', 'Photo 8 category',  'portfolio'),
        ('portfolio_cat_9',          'events',      'text', 'Photo 9 category',  'portfolio'),
        ('portfolio_cat_10',         'travel',      'text', 'Photo 10 category', 'portfolio'),
        ('portfolio_cat_11',         'portraits',   'text', 'Photo 11 category', 'portfolio'),
        ('portfolio_cat_12',         'wedding',     'text', 'Photo 12 category', 'portfolio'),
        ('services_heading',         'Services & Investment',                               'text',  'Page heading',                 'services_page'),
        ('service_detail_1_heading', 'Portraits',                                          'text',  'Service 1 heading',            'services_page'),
        ('service_detail_1_desc',    'Every person carries a story worth telling. Perfecta\'s portrait sessions are relaxed, directed, and focused on one thing — showing you at your most confident and authentic.', 'text', 'Service 1 description', 'services_page'),
        ('service_detail_1_includes','Full edited gallery · Digital files in high resolution · 1–2 hour session · Wardrobe consultation', 'text', 'Service 1 includes', 'services_page'),
        ('service_detail_1_price',   'Starting from ₦50,000',                         'text',  'Service 1 price',              'services_page'),
        ('service_detail_1_image',   '',                                                   'image', 'Service 1 photo',              'services_page'),
        ('service_detail_2_heading', 'Headshots & Corporate',                              'text',  'Service 2 heading',            'services_page'),
        ('service_detail_2_desc',    'First impressions live online now. Whether you\'re a doctor, lawyer, executive, or entrepreneur — a sharp, professional headshot tells people you take your work seriously.', 'text', 'Service 2 description', 'services_page'),
        ('service_detail_2_includes','Individual or team sessions · LinkedIn and press-ready files · Same-week delivery · Studio or on-location', 'text', 'Service 2 includes', 'services_page'),
        ('service_detail_2_price',   'Starting from ₦35,000',                         'text',  'Service 2 price',              'services_page'),
        ('service_detail_2_image',   '',                                                   'image', 'Service 2 photo',              'services_page'),
        ('service_detail_3_heading', 'Maternity & Family',                                 'text',  'Service 3 heading',            'services_page'),
        ('service_detail_3_desc',    'These are the moments you\'ll want to remember exactly as they felt. Warm, unhurried sessions that document new life, growing families, and the people who matter most.', 'text', 'Service 3 description', 'services_page'),
        ('service_detail_3_includes','Bump and newborn sessions available · Full edited gallery · Print-ready files · Studio or outdoor', 'text', 'Service 3 includes', 'services_page'),
        ('service_detail_3_price',   'Starting from ₦60,000',                         'text',  'Service 3 price',              'services_page'),
        ('service_detail_3_image',   '',                                                   'image', 'Service 3 photo',              'services_page'),
        ('service_detail_4_heading', 'Events',                                             'text',  'Service 4 heading',            'services_page'),
        ('service_detail_4_desc',    'Nursing inductions, graduation ceremonies, brand launches, award nights — Perfecta captures the energy and emotion of every milestone with speed and precision.', 'text', 'Service 4 description', 'services_page'),
        ('service_detail_4_includes','Full event coverage · Fast turnaround · Crowd and detail shots · Candid and directed moments', 'text', 'Service 4 includes', 'services_page'),
        ('service_detail_4_price',   'Starting from ₦80,000',                         'text',  'Service 4 price',              'services_page'),
        ('service_detail_4_image',   '',                                                   'image', 'Service 4 photo',              'services_page'),
        ('service_detail_5_heading', 'Brand & Commercial',                                 'text',  'Service 5 heading',            'services_page'),
        ('service_detail_5_desc',    'Your brand deserves imagery that matches its quality. From fashion lookbooks to product campaigns, Perfecta creates content that stops the scroll and sells the vision.', 'text', 'Service 5 description', 'services_page'),
        ('service_detail_5_includes','Creative direction · Full licensed files · Multiple looks · Collaboration with brands and stylists', 'text', 'Service 5 includes', 'services_page'),
        ('service_detail_5_price',   'Starting from ₦150,000',                        'text',  'Service 5 price',              'services_page'),
        ('service_detail_5_image',   '',                                                   'image', 'Service 5 photo',              'services_page'),
        ('about_hero_title',         'Behind the Lens',                                    'text',  'Hero heading',                 'about_page'),
        ('about_hero_sub',           'The story of a photographer obsessed with light and truth.', 'text', 'Hero subtitle',         'about_page'),
        ('about_bio_h2',             'The story behind GlobalPerks',                       'text',  'Bio heading',                  'about_page'),
        ('about_pull_quote',         'GlobalPerks started with one simple thing... people saw beauty in what I captured.', 'text', 'Pull quote', 'about_page'),
        ('about_bio_p1',             'Before GlobalPerks had a name, it had a feeling. Perfecta picked up a camera not because she planned a career, but because people kept stopping to ask about the photos she was taking. What started as curiosity became a calling.', 'text', 'Bio paragraph 1', 'about_page'),
        ('about_bio_p2',             'Based in Calabar and available to travel anywhere the story leads, Perfecta has spent five years building a body of work that spans personal portraits, corporate headshots, maternity sessions, brand campaigns, and live events. Her clients range from fresh graduates marking a milestone to established brands building their visual identity.', 'text', 'Bio paragraph 2', 'about_page'),
        ('about_bio_p3',             'Her approach is simple: make people feel comfortable, then capture them when they forget she\'s there. The result is images that feel both polished and real — because they are.', 'text', 'Bio paragraph 3', 'about_page'),
        ('about_bio_image',          '',                                                   'image', 'Bio photo',                    'about_page'),
        ('about_value_1_word',       'Light',                                              'text',  'Value 1 word',                 'about_page'),
        ('about_value_1_desc',       'Every session is built around beautiful, flattering light.', 'text', 'Value 1 description', 'about_page'),
        ('about_value_2_word',       'People',                                             'text',  'Value 2 word',                 'about_page'),
        ('about_value_2_desc',       'She photographs people, not poses — the real moments land hardest.', 'text', 'Value 2 description', 'about_page'),
        ('about_value_3_word',       'Story',                                              'text',  'Value 3 word',                 'about_page'),
        ('about_value_3_desc',       'Each image is a frame in something larger — your story.', 'text', 'Value 3 description', 'about_page'),
        ('about_cred_1_number',      '295+',                                               'text',  'Credential 1 number',          'about_page'),
        ('about_cred_1_label',       'Sessions Completed',                                 'text',  'Credential 1 label',           'about_page'),
        ('about_cred_2_number',      '5+',                                                 'text',  'Credential 2 number',          'about_page'),
        ('about_cred_2_label',       'Years Shooting',                                     'text',  'Credential 2 label',           'about_page'),
        ('about_cred_3_number',      'Calabar',                                            'text',  'Credential 3 number',          'about_page'),
        ('about_cred_3_label',       'Home Base',                                          'text',  'Credential 3 label',           'about_page'),
        ('about_cta_headline',       "Let’s Create Something Beautiful",              'text',  'CTA headline',                 'about_page'),
        ('about_cta_sub',            'Every great photograph starts with a conversation.', 'text',  'CTA subtext',                  'about_page'),
        ('contact_hero_title',       'Get in Touch',                                       'text',  'Hero heading',                 'contact_page'),
        ('contact_hero_sub',         'Ready to start something? So am I.',                 'text',  'Hero subtitle',                'contact_page'),
        ('contact_h2',               "Let’s Work Together",                           'text',  'Section heading',              'contact_page'),
        ('contact_email',            'hello@globalperks.com',                              'text',  'Contact email (text only)',    'contact_page'),
        ('contact_instagram',        '@globalperks_',                                      'text',  'Instagram handle',             'contact_page'),
        ('contact_instagram_weddings','@globalperks_lovestories',                          'text',  'Weddings Instagram',           'contact_page'),
        ('contact_response_time',    'All enquiries answered within 24 hours',             'text',  'Response time note',           'contact_page'),
        ('contact_location_note',    'Based in Calabar · Available for travel nationwide & beyond', 'text', 'Location note', 'contact_page'),
    ]
    for row in rows:
        conn.execute("""
            INSERT OR IGNORE INTO site_content (key, value, type, label, section)
            VALUES (?, ?, ?, ?, ?)
        """, row)
    conn.commit()
    logger.info(f"Site content seeded with {len(rows)} rows")
