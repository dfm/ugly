# Flask stuff.
DEBUG = False
TESTING = False
SECRET_KEY = "development key"

# App stuff.
ADMIN_EMAIL = "Ugly Reader <ugly@dfm.io>"
BASE_MAILBOX = "[Ugly Reader]"
AES_KEY = b"test AES key... change this in production"
MAX_FEEDS = 100

# Database stuff.
SQLALCHEMY_DATABASE_URI = "postgresql://localhost/ugly"

# Google OAuth stuff.
GOOGLE_OAUTH2_CLIENT_ID = None
GOOGLE_OAUTH2_CLIENT_SECRET = None
