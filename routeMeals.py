import os
import requests
import json
from datetime import datetime, timezone as timezoneUtc
from functools import wraps

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
    @wraps(f)
    def decoratedFunction(*args, **kwargs):
        if "userId" in session:
            user = User.query.get(session["userId"])
            if user:
                return f(*args, **kwargs)
            session.pop("userId", None)
            
        if "tempUser" in session:
            return f(*args, **kwargs)
            
        return redirect(url_for("mealBp.login"))

    return decoratedFunction


@mealBp.route("/")
@loginRequired
def home():
    if "userId" not in session:
        return redirect(url_for("mealBp.onboarding"))
    
    user = User.query.get(session["userId"])
    if not user.fullName:
        return redirect(url_for("mealBp.onboarding"))
    return render_template("index.html", user_name=user.fullName.split()[0], version=datetime.now().timestamp())


@mealBp.route("/login")
def login():
    return render_template("login.html")


@mealBp.route("/google-login")
def googleLogin():
    redirectUri = url_for("mealBp.authorize", _external=True)
    return google.authorize_redirect(redirectUri)


@mealBp.route("/auth/callback")
def authorize():
    token = google.authorize_access_token()
    userInfo = token.get("userinfo")
    if not userInfo:
        resp = google.get("https://www.googleapis.com/oauth2/v3/userinfo")
        userInfo = resp.json()

    user = User.query.filter_by(googleId=userInfo["sub"]).first()
    if not user:
        session.permanent = True
        session["tempUser"] = {
            "googleId": userInfo["sub"],
            "email": userInfo["email"],
            "displayName": userInfo["name"],
            "picture": userInfo.get("picture")
        }
        return redirect(url_for("mealBp.onboarding"))

    session.permanent = True
    session["userId"] = user.id
    return redirect(url_for("mealBp.home"))


@mealBp.route("/api/logout")
def logout():
    session.pop("userId", None)
    session.pop("tempUser", None)
    return {"success": True, "redirect": url_for("mealBp.login")}


@mealBp.route("/onboarding")
@loginRequired
def onboarding():
    return render_template("onboarding.html", version=datetime.now().timestamp())


@mealBp.route("/api/saveProfile", methods=["POST"])
@loginRequired
def saveProfile():
    data = request.get_json()
    
    if "userId" in session:
        user = User.query.get(session["userId"])
        user.fullName = data.get("fullName")
        user.gender = data.get("sex") # Map 'sex' from UI to 'gender' in DB
        user.heightCm = data.get("height") # Map 'height' from UI to 'heightCm' in DB
        user.weight = data.get("weight")
        user.bicepSize = data.get("bicepSize")
        # Handle dateOfBirth if age is provided (approximate for now or update UI later)
        db.session.commit()
    elif "tempUser" in session:
        session["tempUser"].update({
            "fullName": data.get("fullName"),
            "gender": data.get("sex"),
            "heightCm": data.get("height"),
            "weight": data.get("weight"),
            "bicepSize": data.get("bicepSize")
        })
        session.modified = True
    else:
        return {"error": "Not authorized"}, 401
        
    return {"success": True}


@mealBp.route("/api/generateTargets", methods=["POST"])
@loginRequired
def generateTargets():
    data = request.get_json()
    
    if "userId" in session:
        user = User.query.get(session["userId"])
        weight, height, gender = user.weight, user.heightCm, user.gender
        # age calculation logic can be added here using dateOfBirth
        age = 25 # Placeholder for now
    elif "tempUser" in session:
        u = session["tempUser"]
        weight, height, gender = u["weight"], u["heightCm"], u["gender"]
        age = 25 # Placeholder
    else:
        return {"error": "Not authorized"}, 401

    goal = data.get("goal")
    frequency = data.get("frequency")

    apiKey = os.getenv("GEMINI_API_KEY")
    if not apiKey:
        return {"error": "Gemini API key not configured"}, 500

    prompt = (
        f"my weight is {weight} kg, My height is {height} cm and my gender is {gender}. "
        f"I want {goal}. What should be my target calories, protein, fat, carbs and fiber. "
        f"I workout {frequency} times a week please give the output in json format. "
        f"in the json just write the nutritient name as key and amount in values. "
        f"Do not add any message or unit. Just amount needed as key. "
        f"Keys must be protein, calories, fat, carbs, fiber."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={apiKey}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        
        parts = result.get('candidates', [{}])[0].get('content', {}).get('parts', [])
        if not parts:
            return {"error": "Unexpected AI response format"}, 500
            
        content = parts[0]['text']
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        targets = json.loads(content.strip())
        return {"success": True, "targets": targets}
    except Exception as e:
        return {"error": str(e)}, 500


@mealBp.route("/api/saveTargets", methods=["POST"])
@loginRequired
def saveTargets():
    data = request.get_json()
    
    if "userId" in session:
        user = User.query.get(session["userId"])
    elif "tempUser" in session:
        u = session["tempUser"]
        user = User(
            googleId=u["googleId"],
            email=u["email"],
            displayName=u["displayName"],
            picture=u["picture"],
            fullName=u["fullName"],
            gender=u["gender"],
            heightCm=u["heightCm"],
            weight=u["weight"],
            bicepSize=u["bicepSize"]
        )
        db.session.add(user)
        db.session.commit()
        session.permanent = True
        session["userId"] = user.id
        session.pop("tempUser", None)
    else:
        return {"error": "Not authorized"}, 401

    user.targetCalories = data.get("calories")
    user.targetProtein = data.get("protein")
    user.targetCarbs = data.get("carbs")
    user.targetFat = data.get("fat")
    user.targetFiber = data.get("fiber")

    db.session.commit()
    return {"success": True}


@mealBp.route("/api/profile")
@loginRequired
def getProfile():
    user = User.query.get(session["userId"])
    return {
        "fullName": user.fullName,
        "username": user.email,
        "serialNumber": f"NUT-{user.id:04d}",
        "gender": user.gender,
        "height": user.heightCm,
        "weight": user.weight,
        "bicepSize": user.bicepSize,
        "targets": {
            "calories": user.targetCalories,
            "protein": user.targetProtein,
            "carbs": user.targetCarbs,
            "fat": user.targetFat,
            "fiber": user.targetFiber
        }
    }


@mealBp.route("/api/user/targets")
@loginRequired
def getUserTargets():
    user = User.query.get(session["userId"])
    return {
        "calories": user.targetCalories,
        "protein": user.targetProtein,
        "carbs": user.targetCarbs,
        "fat": user.targetFat,
        "fiber": user.targetFiber
    }


@mealBp.route("/api/user/targets", methods=["POST"])
@loginRequired
def updateUserTargets():
    data = request.json
    user = User.query.get(session["userId"])
    
    if not user:
        return {"error": "User not found"}, 404
        
    user.targetCalories = float(data.get("calories", user.targetCalories))
    user.targetProtein = float(data.get("protein", user.targetProtein))
    user.targetCarbs = float(data.get("carbs", user.targetCarbs))
    user.targetFat = float(data.get("fat", user.targetFat))
    user.targetFiber = float(data.get("fiber", user.targetFiber))
    
    db.session.commit()
    return {"message": "Targets updated successfully"}, 200


@mealBp.route("/api/dataBase/directory", methods=["GET"])
@loginRequired
def getFoodDirectory():
    query = request.args.get("q", "").strip()
    
    if not query:
        return {"count": 0, "directory": []}, 200

    if query == "all":
        allFood = FoodDirectory.query.all()
    elif len(query) < 3:
        return {"count": 0, "directory": [], "message": "Search query too short"}, 200
    else:
        allFood = FoodDirectory.query.filter(FoodDirectory.foodName.ilike(f"{query}%")).all()
    
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
    
    required = ["name", "calories", "protein", "carbs", "fat", "fiber"]
    if not all(k in data for k in required):
        return {"error": f"Missing required fields: {required}"}, 400

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
        userId=session["userId"],
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
    mealData = FoodLog.query.filter_by(id=id, userId=session["userId"]).first()

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
    todayDate = datetime.now(timezoneUtc).date()

    stats = (
        db.session.query(
            func.sum(FoodLog.calories).label("calories"),
            func.sum(FoodLog.protein).label("protein"),
            func.sum(FoodLog.carbs).label("carbs"),
            func.sum(FoodLog.fat).label("fat"),
            func.sum(FoodLog.fiber).label("fiber"),
        )
        .filter(func.date(FoodLog.dateLogged) == todayDate)
        .filter(FoodLog.userId == session["userId"])
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
    todayDate = datetime.now(timezoneUtc).date()

    logsForToday = FoodLog.query.filter(
        func.date(FoodLog.dateLogged) == todayDate,
        FoodLog.userId == session["userId"],
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
    logToDelete = FoodLog.query.filter_by(id=id, userId=session["userId"]).first()

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

    todayDate = datetime.now(timezoneUtc).date()
    tempDate = todayDate

    batchSize = 20
    offsetAmount = 0

    logsForAvg = []

    while True:
        logsChunk = (
            FoodLog.query.filter_by(userId=session["userId"])
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
