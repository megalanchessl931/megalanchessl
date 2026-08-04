import os
from app import create_app
from app.config import DevelopmentConfig, ProductionConfig

config = ProductionConfig if os.getenv("FLASK_ENV") == "production" else DevelopmentConfig
app = create_app(config)
