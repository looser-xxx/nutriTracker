from datetime import datetime, timezone

from flask import Blueprint, request
from sqlalchemy import func

from models import FoodDirectory, FoodLog, db

mealBp = Blueprint("mealBp", __name__)


@mealBp.route("/api/admin/addFood", methods=["POST"])
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


@mealBp.route("/api/directory", methods=["GET"])
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


@mealBp.route("/api/logMeal", methods=["POST"])
def logMeal():

    data = request.get_json()

    targetFoodId = data.get("foodId")
    gramsEaten = data.get("amountInG")

    foodItem = FoodDirectory.query.get(targetFoodId)

    if not foodItem:
        return {"error": "Food ID not found in directory. Please add it first."}, 404

    newLog = FoodLog(foodId=targetFoodId, amountInG=gramsEaten)

    db.session.add(newLog)
    db.session.commit()

    return {
        "message": "Meal logged successfully!",
        "details": {
            "foodName": foodItem.foodName,
            "grams": gramsEaten,
            "date": newLog.dateLogged,
        },
    }, 201


def calculateMacros(mealLog):
    food = mealLog.foodItem
    amountInG = mealLog.amountInG
    mult = amountInG / 100

    return {
        "foodName": food.foodName,
        "gramsEaten": amountInG,
        "protein": round(food.protein * mult, 1),
        "calories": round(food.calories * mult, 1),
        "carbs": round(food.carbs * mult, 1),
        "fat": round(food.fat * mult, 1),
        "fiber": round(food.fiber * mult, 1),
    }


@mealBp.route("/api/nutritionConsumed/<int:id>", methods=["GET"])
def nutritionConsumed(id):

    mealData = FoodLog.query.get(id)

    if not mealData:
        return {"error": "meal log not found"}, 404

    calculatedNutrition = calculateMacros(mealData)

    return calculatedNutrition


@mealBp.route("/api/today", methods=["GET"])
def today():
    todayDate = datetime.now(timezone.utc).date()

    logsForToday = FoodLog.query.filter(
        func.date(FoodLog.dateLogged) == todayDate
    ).all()
    dailyMeals = []

    for log in logsForToday:
        mealData = calculateMacros(log)
        dailyMeals.append(mealData)

    return {"date": str(todayDate), "mealsConsumed": dailyMeals}
