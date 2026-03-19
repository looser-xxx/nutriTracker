import json
from app import createApp
from models import db, FoodDirectory

def unload_food_data():
    app = createApp()
    with app.app_context():
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

if __name__ == "__main__":
    unload_food_data()
