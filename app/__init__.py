# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
from dotenv import load_dotenv
import os 

db = SQLAlchemy()

def create_app():
    
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config.from_object("config.Config")

    
    app.config["APCA_API_KEY_ID"] = app.config.get("APCA_API_KEY_ID") or os.getenv("APCA_API_KEY_ID")
    app.config["APCA_API_SECRET_KEY"] = app.config.get("APCA_API_SECRET_KEY") or os.getenv("APCA_API_SECRET_KEY")

    # Provide a safe default if DATABASE_URL wasn’t set
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(app.instance_path) / 'quantmini.db'}"

    db.init_app(app)

    from .api import api_bp 
    app.register_blueprint(api_bp, url_prefix = "/api")
    
    from .dashboard import dashboard_bp 
    app.register_blueprint(dashboard_bp)
                           
    return app
