import json
from app import createApp
from models import db, FoodDirectory

def upload_food_data():
    app = createApp()
    with app.app_context():
        try:
            with open("foodData.json", "r") as f:
                food_list = json.load(f)
        except FileNotFoundError:
            print("foodData.json not found. Please run unloadFoodData.py first.")
            return

        added_count = 0
        updated_count = 0
        
        for food_data in food_list:
            existing_food = FoodDirectory.query.filter_by(foodName=food_data["foodName"]).first()
            
            if existing_food:
                # Update existing entry
                existing_food.calories = food_data["calories"]
                existing_food.protein = food_data["protein"]
                existing_food.carbs = food_data["carbs"]
                existing_food.fat = food_data["fat"]
                existing_food.fiber = food_data["fiber"]
                updated_count += 1
            else:
                # Add new entry
                new_food = FoodDirectory(
                    foodName=food_data["foodName"],
                    calories=food_data["calories"],
                    protein=food_data["protein"],
                    carbs=food_data["carbs"],
                    fat=food_data["fat"],
                    fiber=food_data["fiber"]
                )
                db.session.add(new_food)
                added_count += 1
        
        db.session.commit()
        print(f"Finished uploading data. Added: {added_count}, Updated: {updated_count}")

if __name__ == "__main__":
    upload_food_data()
