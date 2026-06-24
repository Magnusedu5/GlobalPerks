import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
from apps.core.turso import init_db, seed_site_content
init_db()
seed_site_content()
print("Database tables created and site content seeded successfully.")
