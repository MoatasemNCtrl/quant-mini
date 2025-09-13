# config.py
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    # If you don’t set a DB URL in env, fall back to a SQLite file
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "")  # can be empty; we'll set a safe default in __init__.py
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # optional: your Alpaca keys from env
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
    ALPACA_API_SECRET = os.getenv("ALPACA_API_SECRET", "")
