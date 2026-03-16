from app import createApp
from models import db

app = createApp()
with app.app_context():
    db.create_all()
    print("Database tables created/updated successfully.")
