from flask import Blueprint, request

from models import FoodDirectory, FoodLog, db

mealBp = Blueprint("mealBp", __name__)


@mealBp.route("/api/admin/addFood", methods=["POST"])
def addFoodToDataBase():
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
