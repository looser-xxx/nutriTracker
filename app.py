from flask import Flask

from models import db
from routeMeals import mealBp


def createApp():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

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
