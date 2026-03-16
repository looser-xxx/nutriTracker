from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    picture = db.Column(db.String(255), nullable=True)
    
    # Profile fields (Onboarding)
    full_name = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    sex = db.Column(db.String(20), nullable=True)
    height = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    bicep_size = db.Column(db.Float, nullable=True)
    
    # Nutrition Targets
    target_calories = db.Column(db.Float, default=2500.0)
    target_protein = db.Column(db.Float, default=150.0)
    target_carbs = db.Column(db.Float, default=300.0)
    target_fat = db.Column(db.Float, default=80.0)
    target_fiber = db.Column(db.Float, default=30.0)
    
    date_joined = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    logs = db.relationship("FoodLog", backref="user", lazy=True)


class FoodDirectory(db.Model):
    __tablename__ = "foodDirectory"

    id = db.Column(db.Integer, primary_key=True)

    foodName = db.Column(db.String(100), nullable=False, unique=True)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    fiber = db.Column(db.Float, nullable=False)


class FoodLog(db.Model):
    __tablename__ = "foodLog"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True) # Linked to User
    foodName = db.Column(db.String(100), nullable=False)
    amountInG = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    fiber = db.Column(db.Float, nullable=False)
    dateLogged = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
