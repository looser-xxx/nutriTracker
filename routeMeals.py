import os
from datetime import datetime, timezone

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy import func

from models import FoodDirectory, FoodLog, User, db

load_dotenv()

mealBp = Blueprint("mealBp", __name__)

oauth = OAuth()
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def loginRequired(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow access if user is logged in OR if they are in the onboarding process
        if "user_id" in session:
            user = User.query.get(session["user_id"])
            if user:
                return f(*args, **kwargs)
            session.pop("user_id", None)
            
        if "temp_user" in session:
            return f(*args, **kwargs)
            
        return redirect(url_for("mealBp.login"))

    return decorated_function


@mealBp.route("/")
@loginRequired
def home():
    if "user_id" not in session:
        return redirect(url_for("mealBp.onboarding"))
    
    user = User.query.get(session["user_id"])
    if not user.full_name:
        return redirect(url_for("mealBp.onboarding"))
    return render_template("index.html", user_name=user.full_name.split()[0], version=datetime.now().timestamp())


@mealBp.route("/login")
def login():
    return render_template("login.html")


@mealBp.route("/google-login")
def googleLogin():
    redirect_uri = url_for("mealBp.authorize", _external=True)
    return google.authorize_redirect(redirect_uri)


@mealBp.route("/auth/callback")
def authorize():
    token = google.authorize_access_token()
    user_info = token.get("userinfo")
    if not user_info:
        resp = google.get("https://www.googleapis.com/oauth2/v3/userinfo")
        user_info = resp.json()

    user = User.query.filter_by(google_id=user_info["sub"]).first()
    if not user:
        # DO NOT CREATE USER YET. Store info in session for onboarding.
        session.permanent = True
        session["temp_user"] = {
            "google_id": user_info["sub"],
            "email": user_info["email"],
            "name": user_info["name"],
            "picture": user_info.get("picture")
        }
        return redirect(url_for("mealBp.onboarding"))

    session.permanent = True
    session["user_id"] = user.id
    return redirect(url_for("mealBp.home"))


@mealBp.route("/api/logout")
def logout():
    session.pop("user_id", None)
    session.pop("temp_user", None)
    return {"success": True, "redirect": url_for("mealBp.login")}


@mealBp.route("/onboarding")
@loginRequired
def onboarding():
    return render_template("onboarding.html", version=datetime.now().timestamp())


@mealBp.route("/api/saveProfile", methods=["POST"])
@loginRequired
def saveProfile():
    data = request.get_json()
    
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        user.full_name = data.get("fullName")
        user.age = data.get("age")
        user.sex = data.get("sex")
        user.height = data.get("height")
        user.weight = data.get("weight")
        user.bicep_size = data.get("bicepSize")
        db.session.commit()
    elif "temp_user" in session:
        # Update session data
        session["temp_user"].update({
            "full_name": data.get("fullName"),
            "age": data.get("age"),
            "sex": data.get("sex"),
            "height": data.get("height"),
            "weight": data.get("weight"),
            "bicep_size": data.get("bicepSize")
        })
        session.modified = True
    else:
        return {"error": "Not authorized"}, 401
        
    return {"success": True}


@mealBp.route("/api/generateTargets", methods=["POST"])
@loginRequired
def generateTargets():
    import requests
    import json

    data = request.get_json()
    
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        weight, height, age = user.weight, user.height, user.age
    elif "temp_user" in session:
        u = session["temp_user"]
        weight, height, age = u["weight"], u["height"], u["age"]
    else:
        return {"error": "Not authorized"}, 401

    goal = data.get("goal")
    frequency = data.get("frequency")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "Gemini API key not configured"}, 500

    prompt = (
        f"my weight is {weight} kg, My height is {height} cm and my age is {age}. "
        f"I want {goal}. What should be my target calories, protein, fat, carbs and fiber. "
        f"I workout {frequency} times a week please give the output in json format. "
        f"in the json just write the nutritient name as key and amount in values. "
        f"Do not add any message or unit. Just amount needed as key. "
        f"Keys must be protein, calories, fat, carbs, fiber."
    )

    # Fixed URL: using v1beta and gemini-flash-latest alias
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Gemini Response Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Gemini Error Body: {response.text}")
        response.raise_for_status()
        result = response.json()
        
        # Extract JSON from Gemini response
        parts = result.get('candidates', [{}])[0].get('content', {}).get('parts', [])
        if not parts:
            print(f"Gemini unexpected result structure: {result}")
            return {"error": "Unexpected AI response format"}, 500
            
        content = parts[0]['text']
        # Remove markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        targets = json.loads(content.strip())
        return {"success": True, "targets": targets}
    except Exception as e:
        print(f"Gemini API error: {e}")
        return {"error": str(e)}, 500


@mealBp.route("/api/saveTargets", methods=["POST"])
@loginRequired
def saveTargets():
    data = request.get_json()
    
    if "user_id" in session:
        user = User.query.get(session["user_id"])
    elif "temp_user" in session:
        # FINAL STEP: Create user in database now
        u = session["temp_user"]
        user = User(
            google_id=u["google_id"],
            email=u["email"],
            name=u["name"],
            picture=u["picture"],
            full_name=u["full_name"],
            age=u["age"],
            sex=u["sex"],
            height=u["height"],
            weight=u["weight"],
            bicep_size=u["bicep_size"]
        )
        db.session.add(user)
        db.session.commit()
        session.permanent = True
        session["user_id"] = user.id
        session.pop("temp_user", None)
    else:
        return {"error": "Not authorized"}, 401

    user.target_calories = data.get("calories")
    user.target_protein = data.get("protein")
    user.target_carbs = data.get("carbs")
    user.target_fat = data.get("fat")
    user.target_fiber = data.get("fiber")

    db.session.commit()
    return {"success": True}


@mealBp.route("/api/profile")
@loginRequired
def getProfile():
    user = User.query.get(session["user_id"])
    return {
        "fullName": user.full_name,
        "username": user.email,
        "serialNumber": f"NUT-{user.id:04d}",
        "age": user.age,
        "sex": user.sex,
        "height": user.height,
        "weight": user.weight,
        "bicepSize": user.bicep_size,
        "targets": {
            "calories": user.target_calories,
            "protein": user.target_protein,
            "carbs": user.target_carbs,
            "fat": user.target_fat,
            "fiber": user.target_fiber
        }
    }


@mealBp.route("/api/user/targets")
@loginRequired
def getUserTargets():
    user = User.query.get(session["user_id"])
    return {
        "calories": user.target_calories,
        "protein": user.target_protein,
        "carbs": user.target_carbs,
        "fat": user.target_fat,
        "fiber": user.target_fiber
    }


@mealBp.route("/api/user/targets", methods=["POST"])
@loginRequired
def updateUserTargets():
    data = request.json
    user = User.query.get(session["user_id"])
    
    if not user:
        return {"error": "User not found"}, 404
        
    user.target_calories = float(data.get("calories", user.target_calories))
    user.target_protein = float(data.get("protein", user.target_protein))
    user.target_carbs = float(data.get("carbs", user.target_carbs))
    user.target_fat = float(data.get("fat", user.target_fat))
    user.target_fiber = float(data.get("fiber", user.target_fiber))
    
    db.session.commit()
    return {"message": "Targets updated successfully"}, 200


@mealBp.route("/api/dataBase/directory", methods=["GET"])
@loginRequired
def getFoodDirectory():
    query = request.args.get("q", "").strip()
    print(f"DEBUG: Directory search requested. Query: '{query}'")
    
    if not query:
        return {"count": 0, "directory": []}, 200

    if query == "all":
        allFood = FoodDirectory.query.all()
    elif len(query) < 3:
        return {"count": 0, "directory": [], "message": "Search query too short"}, 200
    else:
        # Match items STARTING with the query (case-insensitive)
        allFood = FoodDirectory.query.filter(FoodDirectory.foodName.ilike(f"{query}%")).all()
    
    print(f"DEBUG: Found {len(allFood)} results for '{query}'")
    
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


@mealBp.route("/api/dataBase/addFood", methods=["POST"])
@loginRequired
def addFood():
    data = request.get_json()
    
    # Basic validation
    required = ["name", "calories", "protein", "carbs", "fat", "fiber"]
    if not all(k in data for k in required):
        return {"error": f"Missing required fields: {required}"}, 400

    # Check if already exists
    existing = FoodDirectory.query.filter_by(foodName=data['name']).first()
    if existing:
        return {"error": "Food already exists in directory"}, 400

    newFood = FoodDirectory(
        foodName=data['name'],
        calories=data['calories'],
        protein=data['protein'],
        carbs=data['carbs'],
        fat=data['fat'],
        fiber=data['fiber']
    )

    db.session.add(newFood)
    db.session.commit()

    return {"success": True, "id": newFood.id}, 201


@mealBp.route("/api/logs/logMeal", methods=["POST"])
@loginRequired
def logMeal():

    data = request.get_json()

    targetId = data.get("foodId")
    gramsEaten = data.get("amountInG")

    foodItem = FoodDirectory.query.get(targetId)

    if not foodItem:
        return {"error": "Food ID not found in directory. Please add it first."}, 404

    macros = calculateSnapshotMacros(foodItem, gramsEaten)

    newLog = FoodLog(
        user_id=session["user_id"],
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
@loginRequired
def nutritionConsumed(id):

    mealData = FoodLog.query.filter_by(id=id, user_id=session["user_id"]).first()

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


@mealBp.route("/api/logs/today/totalNutriConsumed", methods=["GET"])
@loginRequired
def totalNutriConsumed():
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
        .filter(FoodLog.user_id == session["user_id"])
        .first()
    )

    return {
        "calories": round(stats.calories or 0, 1),
        "protein": round(stats.protein or 0, 1),
        "carbs": round(stats.carbs or 0, 1),
        "fat": round(stats.fat or 0, 1),
        "fiber": round(stats.fiber or 0, 1),
    }


@mealBp.route("/api/logs/today/allLogs", methods=["GET"])
@loginRequired
def today():
    todayDate = datetime.now(timezone.utc).date()

    logsForToday = FoodLog.query.filter(
        func.date(FoodLog.dateLogged) == todayDate,
        FoodLog.user_id == session["user_id"],
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


@mealBp.route("/api/logs/today/delete/<int:id>", methods=["DELETE"])
@loginRequired
def deleteFood(id):
    logToDelete = FoodLog.query.filter_by(id=id, user_id=session["user_id"]).first()

    if not logToDelete:
        return {"error": "Log not found"}, 404

    db.session.delete(logToDelete)
    db.session.commit()

    return {"id": id}, 200


@mealBp.route("/api/logs/avg/<int:days>", methods=["GET"])
@loginRequired
def sendAvg(days):
    return calculateAvg(getLogsForAvg(days), days)


def getLogsForAvg(days):
    daysPassedCount = 0
    targetCount = days

    todayDate = datetime.now(timezone.utc).date()
    tempDate = todayDate

    batchSize = 20
    offsetAmount = 0

    logsForAvg = []

    while True:
        logsChunk = (
            FoodLog.query.filter_by(user_id=session["user_id"])
            .order_by(FoodLog.dateLogged.desc())
            .limit(batchSize)
            .offset(offsetAmount)
            .all()
        )

        if not logsChunk:
            break

        for log in logsChunk:

            if log.dateLogged:
                logDate = log.dateLogged.date()
            else:
                logDate = None

            if logDate == todayDate:
                continue

            if logDate != tempDate:
                tempDate = logDate
                daysPassedCount += 1

            if daysPassedCount > targetCount:
                return logsForAvg

            logsForAvg.append(log)

        offsetAmount += batchSize

    return logsForAvg


def calculateAvg(logs, days):
    calories = 0
    protein = 0
    carbs = 0
    fat = 0
    fiber = 0
    graphData = []

    for log in logs:
        calories += log.calories
        graphData.append(log.calories)
        protein += log.protein
        carbs += log.carbs
        fat += log.fat
        fiber += log.fiber

    days = max(days, 1)
    return {
        "average": {
            "calories": round(calories / days, 1),
            "protein": round(protein / days, 1),
            "carbs": round(carbs / days, 1),
            "fat": round(fat / days, 1),
            "fiber": round(fiber / days, 1),
        },
        "graphData": graphData,
        "daysFound": days,
    }
