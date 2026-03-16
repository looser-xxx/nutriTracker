import os
from datetime import datetime, timezone

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy import func

from models import FoodDirectory, FoodLog, User, db

load_dotenv()

mealBp = Blueprint("mealBp", __name__)

oauth = OAuth()
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    client_kwargs={"scope": "openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
)


def loginRequired(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("mealBp.login"))
        return f(*args, **kwargs)

    return decorated_function


@mealBp.route("/")
@loginRequired
def home():
    user = User.query.get(session["user_id"])
    if not user.full_name:
        return redirect(url_for("mealBp.onboarding"))
    return render_template("index.html", user_name=user.full_name.split()[0])


@mealBp.route("/login")
def login():
    return render_template("login.html")


@mealBp.route("/google-login")
def googleLogin():
    redirect_uri = url_for("mealBp.authorize", _external=True)
    return google.authorize_redirect(redirect_uri)


@mealBp.route("/auth/callback")
def authorize():
    token = google.authorize_access_token()
    resp = google.get("userinfo")
    user_info = resp.json()

    user = User.query.filter_by(google_id=user_info["id"]).first()
    if not user:
        user = User(
            google_id=user_info["id"],
            email=user_info["email"],
            name=user_info["name"],
            picture=user_info.get("picture"),
        )
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    return redirect(url_for("mealBp.home"))


@mealBp.route("/api/logout")
def logout():
    session.pop("user_id", None)
    return {"success": True, "redirect": url_for("mealBp.login")}


@mealBp.route("/onboarding")
@loginRequired
def onboarding():
    return render_template("onboarding.html")


@mealBp.route("/api/saveProfile", methods=["POST"])
@loginRequired
def saveProfile():
    data = request.get_json()
    user = User.query.get(session["user_id"])

    user.full_name = data.get("fullName")
    user.age = data.get("age")
    user.sex = data.get("sex")
    user.height = data.get("height")
    user.weight = data.get("weight")
    user.bicep_size = data.get("bicepSize")

    db.session.commit()
    return {"success": True}


@mealBp.route("/api/profile")
@loginRequired
def getProfile():
    user = User.query.get(session["user_id"])
    return {
        "fullName": user.full_name,
        "username": user.email,
        "serialNumber": f"NUT-{user.id:04d}",
        "age": user.age,
        "sex": user.sex,
        "height": user.height,
        "weight": user.weight,
        "bicepSize": user.bicep_size,
    }


@mealBp.route("/api/dataBase/directory", methods=["GET"])
@loginRequired
def getFoodDirectory():
    allFood = FoodDirectory.query.all()
    output = []
    for food in allFood:
        output.append(
            {
                "id": food.id,
                "name": food.foodName,
                "macros": {
                    "cal": food.calories,
                    "p": food.protein,
                    "c": food.carbs,
                    "f": food.fat,
                    "fib": food.fiber,
                },
            }
        )
    return {"count": len(output), "directory": output}, 200


@mealBp.route("/api/logs/logMeal", methods=["POST"])
@loginRequired
def logMeal():

    data = request.get_json()

    targetId = data.get("foodId")
    gramsEaten = data.get("amountInG")

    foodItem = FoodDirectory.query.get(targetId)

    if not foodItem:
        return {"error": "Food ID not found in directory. Please add it first."}, 404

    macros = calculateSnapshotMacros(foodItem, gramsEaten)

    newLog = FoodLog(
        user_id=session["user_id"],
        foodName=foodItem.foodName,
        amountInG=gramsEaten,
        calories=macros["calories"],
        protein=macros["protein"],
        carbs=macros["carbs"],
        fat=macros["fat"],
        fiber=macros["fiber"],
    )

    db.session.add(newLog)
    db.session.commit()

    return {
        "message": "Meal logged successfully!",
        "details": {
            "foodName": newLog.foodName,
            "grams": newLog.amountInG,
            "calories": newLog.calories,
            "date": (
                newLog.dateLogged.strftime("%Y-%m-%d") if newLog.dateLogged else None
            ),
        },
    }, 201


def calculateSnapshotMacros(foodItem, grams):
    multiplier = grams / 100

    return {
        "calories": round(foodItem.calories * multiplier, 1),
        "protein": round(foodItem.protein * multiplier, 1),
        "carbs": round(foodItem.carbs * multiplier, 1),
        "fat": round(foodItem.fat * multiplier, 1),
        "fiber": round(foodItem.fiber * multiplier, 1),
    }


@mealBp.route("/api/logs/nutritionConsumed/<int:id>", methods=["GET"])
@loginRequired
def nutritionConsumed(id):

    mealData = FoodLog.query.filter_by(id=id, user_id=session["user_id"]).first()

    if not mealData:
        return {"error": "meal log not found"}, 404

    fetchedNutrition = {
        "logId": mealData.id,
        "foodName": mealData.foodName,
        "gramsEaten": mealData.amountInG,
        "protein": mealData.protein,
        "calories": mealData.calories,
        "carbs": mealData.carbs,
        "fat": mealData.fat,
        "fiber": mealData.fiber,
        "date": (
            mealData.dateLogged.strftime("%Y-%m-%d") if mealData.dateLogged else None
        ),
    }

    return fetchedNutrition


@mealBp.route("/api/logs/today/totalNutriConsumed", methods=["GET"])
@loginRequired
def totalNutriConsumed():
    todayDate = datetime.now(timezone.utc).date()

    stats = (
        db.session.query(
            func.sum(FoodLog.calories).label("calories"),
            func.sum(FoodLog.protein).label("protein"),
            func.sum(FoodLog.carbs).label("carbs"),
            func.sum(FoodLog.fat).label("fat"),
            func.sum(FoodLog.fiber).label("fiber"),
        )
        .filter(func.date(FoodLog.dateLogged) == todayDate)
        .filter(FoodLog.user_id == session["user_id"])
        .first()
    )

    return {
        "calories": round(stats.calories or 0, 1),
        "protein": round(stats.protein or 0, 1),
        "carbs": round(stats.carbs or 0, 1),
        "fat": round(stats.fat or 0, 1),
        "fiber": round(stats.fiber or 0, 1),
    }


@mealBp.route("/api/logs/today/allLogs", methods=["GET"])
@loginRequired
def today():
    todayDate = datetime.now(timezone.utc).date()

    logsForToday = FoodLog.query.filter(
        func.date(FoodLog.dateLogged) == todayDate,
        FoodLog.user_id == session["user_id"],
    ).all()

    dailyMeals = []

    for log in logsForToday:
        mealData = {
            "logId": log.id,
            "foodName": log.foodName,
            "gramsEaten": log.amountInG,
            "protein": log.protein,
            "calories": log.calories,
            "carbs": log.carbs,
            "fat": log.fat,
            "fiber": log.fiber,
        }
        dailyMeals.append(mealData)

    return {"date": str(todayDate), "mealsConsumed": dailyMeals}


@mealBp.route("/api/logs/today/delete/<int:id>", methods=["DELETE"])
@loginRequired
def deleteFood(id):
    logToDelete = FoodLog.query.filter_by(id=id, user_id=session["user_id"]).first()

    if not logToDelete:
        return {"error": "Log not found"}, 404

    db.session.delete(logToDelete)
    db.session.commit()

    return {"id": id}, 200


@mealBp.route("/api/logs/avg/<int:days>", methods=["GET"])
@loginRequired
def sendAvg(days):
    return calculateAvg(getLogsForAvg(days), days)


def getLogsForAvg(days):
    daysPassedCount = 0
    targetCount = days

    todayDate = datetime.now(timezone.utc).date()
    tempDate = todayDate

    batchSize = 20
    offsetAmount = 0

    logsForAvg = []

    while True:
        logsChunk = (
            FoodLog.query.filter_by(user_id=session["user_id"])
            .order_by(FoodLog.dateLogged.desc())
            .limit(batchSize)
            .offset(offsetAmount)
            .all()
        )

        if not logsChunk:
            break

        for log in logsChunk:

            if log.dateLogged:
                logDate = log.dateLogged.date()
            else:
                logDate = None

            if logDate == todayDate:
                continue

            if logDate != tempDate:
                tempDate = logDate
                daysPassedCount += 1

            if daysPassedCount > targetCount:
                return logsForAvg

            logsForAvg.append(log)

        offsetAmount += batchSize

    return logsForAvg


def calculateAvg(logs, days):
    calories = 0
    protein = 0
    carbs = 0
    fat = 0
    fiber = 0
    graphData = []

    for log in logs:
        calories += log.calories
        graphData.append(log.calories)
        protein += log.protein
        carbs += log.carbs
        fat += log.fat
        fiber += log.fiber

    days = max(days, 1)
    return {
        "average": {
            "calories": round(calories / days, 1),
            "protein": round(protein / days, 1),
            "carbs": round(carbs / days, 1),
            "fat": round(fat / days, 1),
            "fiber": round(fiber / days, 1),
        },
        "graphData": graphData,
        "daysFound": days,
    }
