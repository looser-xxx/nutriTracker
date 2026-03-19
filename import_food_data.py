import csv
import json
import os

csv_path = 'foodDataSet/Indian_Food_Nutrition_Processed.csv'
json_path = 'foodData.json'

def clean_val(val):
    if not val or val.strip() == '':
        return 0.0
    try:
        # Just in case there are units like "kcal" or "g" in the actual cells
        return float(''.join(c for c in str(val) if c.isdigit() or c == '.'))
    except ValueError:
        return 0.0

# Load existing data
if os.path.exists(json_path):
    with open(json_path, 'r') as f:
        food_list = json.load(f)
else:
    food_list = []

# Map existing names for duplicate check (case-insensitive)
existing_names = {item['foodName'].strip().lower() for item in food_list}

new_items_count = 0

# Read CSV
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row.get('Dish Name', '').strip()
        if not name or name.lower() in existing_names:
            continue
        
        item = {
            "foodName": name,
            "calories": clean_val(row.get('Calories (kcal)', 0)),
            "protein": clean_val(row.get('Protein (g)', 0)),
            "carbs": clean_val(row.get('Carbohydrates (g)', 0)),
            "fat": clean_val(row.get('Fats (g)', 0)),
            "fiber": clean_val(row.get('Fibre (g)', 0))
        }
        
        food_list.append(item)
        existing_names.add(name.lower())
        new_items_count += 1

# Write back to JSON
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(food_list, f, indent=4)

print(f"Successfully added {new_items_count} new food items to {json_path}")
