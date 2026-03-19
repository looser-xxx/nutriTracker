import json
from app import createApp
from models import db, FoodDirectory, ExerciseDirectory

def unload_database():
    app = createApp()
    with app.app_context():
        # Unload Food
        foods = FoodDirectory.query.all()
        food_list = []
        for food in foods:
            food_list.append({
                "foodName": food.foodName,
                "calories": food.calories,
                "protein": food.protein,
                "carbs": food.carbs,
                "fat": food.fat,
                "fiber": food.fiber
            })
        
        with open("foodData.json", "w") as f:
            json.dump(food_list, f, indent=4)
        print(f"Successfully unloaded {len(food_list)} food items to foodData.json")

        # Unload Exercises
        exercises = ExerciseDirectory.query.all()
        exercise_list = []
        for ex in exercises:
            exercise_list.append({
                "exerciseName": ex.exerciseName,
                "targetMuscleGroup": ex.targetMuscleGroup,
                "movementType": ex.movementType,
                "equipmentNeeded": ex.equipmentNeeded,
                "caloriesPerRep": ex.caloriesPerRep
            })
        
        with open("exerciseData.json", "w") as f:
            json.dump(exercise_list, f, indent=4)
        print(f"Successfully unloaded {len(exercise_list)} exercises to exerciseData.json")

if __name__ == "__main__":
    unload_database()
