import json
import os
from app import createApp
from models import db, FoodDirectory, ExerciseDirectory

def upload_database():
    app = createApp()
    with app.app_context():
        # Upload Food
        if os.path.exists("foodData.json"):
            with open("foodData.json", "r") as f:
                food_list = json.load(f)
            
            added = 0
            updated = 0
            for data in food_list:
                existing = FoodDirectory.query.filter_by(foodName=data["foodName"]).first()
                if existing:
                    existing.calories = data["calories"]
                    existing.protein = data["protein"]
                    existing.carbs = data["carbs"]
                    existing.fat = data["fat"]
                    existing.fiber = data["fiber"]
                    updated += 1
                else:
                    new_food = FoodDirectory(
                        foodName=data["foodName"],
                        calories=data["calories"],
                        protein=data["protein"],
                        carbs=data["carbs"],
                        fat=data["fat"],
                        fiber=data["fiber"]
                    )
                    db.session.add(new_food)
                    added += 1
            print(f"Food Upload: Added {added}, Updated {updated}")
        else:
            print("foodData.json not found.")

        # Upload Exercises
        if os.path.exists("exerciseData.json"):
            with open("exerciseData.json", "r") as f:
                exercise_list = json.load(f)
            
            added = 0
            updated = 0
            for data in exercise_list:
                existing = ExerciseDirectory.query.filter_by(exerciseName=data["exerciseName"]).first()
                if existing:
                    existing.targetMuscleGroup = data["targetMuscleGroup"]
                    existing.movementType = data["movementType"]
                    existing.equipmentNeeded = data["equipmentNeeded"]
                    existing.caloriesPerRep = data.get("caloriesPerRep", 0.0)
                    updated += 1
                else:
                    new_ex = ExerciseDirectory(
                        exerciseName=data["exerciseName"],
                        targetMuscleGroup=data["targetMuscleGroup"],
                        movementType=data["movementType"],
                        equipmentNeeded=data["equipmentNeeded"],
                        caloriesPerRep=data.get("caloriesPerRep", 0.0)
                    )
                    db.session.add(new_ex)
                    added += 1
            print(f"Exercise Upload: Added {added}, Updated {updated}")
        else:
            print("exerciseData.json not found.")

        db.session.commit()
        print("Database sync completed.")

if __name__ == "__main__":
    upload_database()
