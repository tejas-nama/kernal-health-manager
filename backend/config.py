import secrets

# --- APPLICATION SETTINGS ---
APP_NAME = "Kernel Health Monitor"
DB_PATH = "kernel_monitor.db" 

# --- SECURITY SETTINGS ---
# This was missing or named incorrectly in your file
SECRET_KEY = secrets.token_urlsafe(32) 

ALGORITHM = "HS256" 
ACCESS_TOKEN_EXPIRE_MINUTES = 60