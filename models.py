from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    googleId = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    displayName = db.Column(db.String(100), nullable=True)
    picture = db.Column(db.String(255), nullable=True)
    
    # Biometrics & Identity
    fullName = db.Column(db.String(100), nullable=True)
    dateOfBirth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    heightCm = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    bicepSize = db.Column(db.Float, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    
    # User Goals & Settings
    goalType = db.Column(db.String(50), nullable=True)
    activityLevel = db.Column(db.String(50), nullable=True)
    timezone = db.Column(db.String(50), default="UTC")
    
    # Nutrition Targets
    targetCalories = db.Column(db.Float, default=2500.0)
    targetProtein = db.Column(db.Float, default=150.0)
    targetCarbs = db.Column(db.Float, default=300.0)
    targetFat = db.Column(db.Float, default=80.0)
    targetFiber = db.Column(db.Float, default=30.0)
    
    # System Data
    createdAt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    lastActive = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    foodLogs = db.relationship("FoodLog", backref="user", lazy=True)
    hydrationLogs = db.relationship("HydrationLog", backref="user", lazy=True)
    workoutSessions = db.relationship("WorkoutSession", backref="user", lazy=True)
    progressLogs = db.relationship("ProgressLog", backref="user", lazy=True)


class ProgressLog(db.Model):
    __tablename__ = "progressLog"

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    weightKg = db.Column(db.Float, nullable=False)
    bodyFatPercentage = db.Column(db.Float, nullable=True)
    bicepSizeCm = db.Column(db.Float, nullable=True)
    chestSizeCm = db.Column(db.Float, nullable=True)
    waistSizeCm = db.Column(db.Float, nullable=True)
    thighSizeCm = db.Column(db.Float, nullable=True)
    loggedAt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


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
    userId = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    foodName = db.Column(db.String(100), nullable=False)
    amountInG = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    fiber = db.Column(db.Float, nullable=False)
    dateLogged = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class HydrationLog(db.Model):
    __tablename__ = "hydrationLog"

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amountMl = db.Column(db.Float, nullable=False)
    beverageType = db.Column(db.String(50), default="Water")
    loggedAt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class WorkoutSession(db.Model):
    __tablename__ = "workoutSession"

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    sessionType = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    loggedAt = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    exercises = db.relationship("ExerciseSet", backref="session", lazy=True)

    @property
    def totalCaloriesBurned(self):
        total = 0
        for set_entry in self.exercises:
            if set_entry.exercise and set_entry.exercise.caloriesPerRep:
                total += set_entry.reps * set_entry.exercise.caloriesPerRep
        return round(total, 1)


class ExerciseDirectory(db.Model):
    __tablename__ = "exerciseDirectory"

    id = db.Column(db.Integer, primary_key=True)
    exerciseName = db.Column(db.String(100), nullable=False, unique=True)
    targetMuscleGroup = db.Column(db.String(100), nullable=True)
    movementType = db.Column(db.String(50), nullable=True)
    equipmentNeeded = db.Column(db.String(100), nullable=True)
    caloriesPerRep = db.Column(db.Float, default=0.0)
    
    sets = db.relationship("ExerciseSet", backref="exercise", lazy=True)


class ExerciseSet(db.Model):
    __tablename__ = "exerciseSet"

    id = db.Column(db.Integer, primary_key=True)
    sessionId = db.Column(db.Integer, db.ForeignKey("workoutSession.id"), nullable=False)
    exerciseId = db.Column(db.Integer, db.ForeignKey("exerciseDirectory.id"), nullable=False)
    setNumber = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weightKg = db.Column(db.Float, nullable=False)
