# Flask stuff.
DEBUG = False
TESTING = False
SECRET_KEY = "development key"

# App stuff.
ADMIN_EMAIL = "Ugly RSS <ugly@dfm.io>"
AES_KEY = b"test AES key... change this in production"

# Database stuff.
SQLALCHEMY_DATABASE_URI = "postgresql://localhost/ugly"

# Google OAuth stuff.
GOOGLE_OAUTH2_CLIENT_ID = None
GOOGLE_OAUTH2_CLIENT_SECRET = None
