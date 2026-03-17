import os

from datetime import timedelta
from dotenv import load_dotenv
from flask import Flask

from models import db
from routeMeals import mealBp, oauth

from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()


def createApp():
    app = Flask(__name__)
    
    # Handle Proxy (Cloudflare Tunnel)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

    # Production HTTPS settings
    if not app.debug:
        app.config["SESSION_COOKIE_SECURE"] = True

    db.init_app(app)
    oauth.init_app(app)

    app.register_blueprint(mealBp)

    @app.errorhandler(404)
    def resourceNotFound(error):
        return {"error": "The requested URL or resource was not found."}, 404

    @app.errorhandler(500)
    def internalServerError(error):
        return {"error": "An unexpected server error occurred. Check your code!"}, 500

    @app.errorhandler(400)
    def badRequest(error):
        return {"error": "Bad request. Please ensure you are sending valid JSON."}, 400

    return app


if __name__ == "__main__":
    nutTrackApp = createApp()
    nutTrackApp.run(debug=True)
