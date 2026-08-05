import os
from app import create_app
from app.config import DevelopmentConfig, ProductionConfig

config = ProductionConfig if os.getenv("FLASK_ENV") == "production" else DevelopmentConfig
app = create_app(config)

# adicionado para 2 computadores
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
