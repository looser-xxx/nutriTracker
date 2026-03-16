from datetime import datetime, timezone

from flask import Blueprint, render_template, request
from sqlalchemy import func

from models import FoodDirectory, FoodLog, db

mealBp = Blueprint("mealBp", __name__)


@mealBp.route("/")
def home():
    return render_template("index.html")


@mealBp.route("/api/dataBase/admin/addFood", methods=["POST"])
def addFoodToDirectory():
    data = request.get_json()

    requiredFields = ["foodName", "calories", "protein", "carbs", "fat", "fiber"]
    for field in requiredFields:
        if field not in data:
            return {"error": f"Missing field: {field}"}, 400

    if data.get("adminPassword") != "lightWeightBaby":
        return {"error": "Unauthorized access"}, 401

    newFood = FoodDirectory(
        foodName=data["foodName"],
        calories=data["calories"],
        protein=data["protein"],
        carbs=data["carbs"],
        fat=data["fat"],
        fiber=data["fiber"],
    )

    try:
        db.session.add(newFood)
        db.session.commit()
        return {
            "message": f"{newFood.foodName} added to dataBase",
            "id": newFood.id,
        }, 201
    except Exception as e:
        db.session.rollback()
        return {"error": f"Food name already exists or database error: {e}"}, 400


@mealBp.route("/api/dataBase/directory", methods=["GET"])
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
def logMeal():

    data = request.get_json()

    targetId = data.get("foodId")
    gramsEaten = data.get("amountInG")

    foodItem = FoodDirectory.query.get(targetId)

    if not foodItem:
        return {"error": "Food ID not found in directory. Please add it first."}, 404

    macros = calculateSnapshotMacros(foodItem, gramsEaten)

    newLog = FoodLog(
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
def nutritionConsumed(id):

    mealData = FoodLog.query.get(id)

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


@mealBp.route("/api/logs/today/allLogs", methods=["GET"])
def today():
    todayDate = datetime.now(timezone.utc).date()

    logsForToday = FoodLog.query.filter(
        func.date(FoodLog.dateLogged) == todayDate
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


@mealBp.route("/api/logs/today/totalNutriConsumed", methods=["GET"])
@mealBp.route("/api/todayStats", methods=["GET"])
def getTodayStats():
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
        .first()
    )

    return {
        "calories": round(stats.calories or 0, 1),
        "protein": round(stats.protein or 0, 1),
        "carbs": round(stats.carbs or 0, 1),
        "fat": round(stats.fat or 0, 1),
        "fiber": round(stats.fiber or 0, 1),
    }


@mealBp.route("/api/logs/today/delete/<int:id>", methods=["DELETE"])
def deleteFood(id):
    logToDelete = FoodLog.query.get(id)

    if not logToDelete:
        return {"error": "Log not found"}, 404

    db.session.delete(logToDelete)
    db.session.commit()

    return {"id": id}, 200


# sldf
