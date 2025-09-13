# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    app.config.from_object("config.Config")

    # Provide a safe default if DATABASE_URL wasn’t set
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Path(app.instance_path) / 'quantmini.db'}"

    db.init_app(app)

    from .api import api_bp 
    app.register_blueprint(api_bp, url_prefix = "/api")
    
    from .dashboard import dashboard_bp 
    app.register_blueprint(dashboard_bp)
                           
    return app
