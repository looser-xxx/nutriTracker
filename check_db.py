from app import createApp
from models import FoodDirectory, db
import sys

app = createApp()
with app.app_context():
    try:
        allFood = FoodDirectory.query.all()
        print(f"Success: Found {len(allFood)} items.")
    except Exception as e:
        print(f"CRITICAL_ERROR: {str(e)}")
        sys.exit(1)
