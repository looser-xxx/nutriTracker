from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class FoodDirectory(db.Model):
    __tablename__ = "foodDirectory"

    id = db.Column(db.Integer, primary_key=True)

    foodName = db.Column(db.String(100), nullable=False, unique=True)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    fiber = db.Column(db.Float, nullable=False)

    logs = db.relationship("FoodLog", backref="foodItem", lazy=True)


class FoodLog(db.Model):
    __tablename__ = "foodLog"

    id = db.Column(db.Integer, primary_key=True)
    foodId = db.Column(db.Integer, db.ForeignKey("foodDirectory.id"), nullable=False)
    amountInG = db.Column(db.Float, nullable=False)
    dateLogged = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
