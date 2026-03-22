import os
import requests
import json
from datetime import datetime, timezone
from functools import wraps

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Blueprint, redirect, render_template, request, session, url_for
from sqlalchemy import func

from models import FoodDirectory, FoodLog, HydrationLog, User, db

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


@mealBp.route("/workout")
@loginRequired
def workout():
    if "userId" not in session:
        return redirect(url_for("mealBp.onboarding"))
    return render_template("under_development.html", section="Workout", version=datetime.now().timestamp())


@mealBp.route("/hydration")
@loginRequired
def hydration():
    user = User.query.get(session["userId"])
    return render_template("hydration.html", user_name=user.fullName.split()[0], version=datetime.now().timestamp())


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

    # Extract all user data from request
    goal = data.get("goal")
    frequency = data.get("frequency")
    age = data.get("age")
    sex = data.get("sex")
    height = data.get("height")
    weight = data.get("weight")
    bicepSize = data.get("bicepSize")

    prompt = (
        f"my weight is {weight} kg, my height is {height} cm, my age is {age} and my sex is {sex}. "
        f"My current bicep size is {bicepSize} inches. "
        f"My fitness goal is '{goal}'. "
        f"I workout {frequency} times a week. "
        f"Please calculate what should be my daily target for calories (kcal), protein (g), fat (g), carbs (g), and fiber (g). "
        f"Provide the output ONLY in JSON format. "
        f"In the JSON, use the nutrient name as the key and the numeric amount as the value. "
        f"Do not add any message, explanation, or units. "
        f"Keys MUST be: protein, calories, fat, carbs, fiber."
    )

    # Call local Ollama instead of Gemini
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.2:3b",
        "prompt": prompt,
        "format": "json",
        "stream": False
    }

    print(f"DEBUG: Ollama generateTargets Prompt: {prompt}")

    try:
        response = requests.post(url, json=payload)
        print(f"DEBUG: Ollama generateTargets Status: {response.status_code}")
        response.raise_for_status()
        result = response.json()

        content = result.get('response', '')
        print(f"DEBUG: Ollama generateTargets Content: {content}")
        if not content:
            return {"error": "Unexpected AI response format"}, 500

        # Extract JSON if it's wrapped in markdown or contains extra text
        import re
        import json
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            content = json_match.group(0)
        
        targets = json.loads(content.strip())
        return {"success": True, "targets": targets}
    except Exception as e:
        print(f"Error generating targets: {str(e)}")
        return {"error": f"Failed to generate targets: {str(e)}"}, 500


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
        "fiber": user.targetFiber,
        "water": user.targetWater
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
    user.targetWater = float(data.get("water", user.targetWater))
    
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


@mealBp.route("/admin.html")
def adminPage():
    return render_template("admin.html")


@mealBp.route("/api/admin/addFood", methods=["POST"])
def adminAddFood():
    data = request.get_json()
    password = data.get("password")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not password or password != admin_password:
        return {"error": "wrong password"}, 401

    food_name = data.get("foodName")
    calories = data.get("calories")
    protein = data.get("protein")
    carbs = data.get("carbs")
    fat = data.get("fat")
    fiber = data.get("fiber")

    if not food_name:
        return {"error": "Food Name is required"}, 400

    # Check if food already exists in DB
    existing = FoodDirectory.query.filter_by(foodName=food_name).first()
    if existing:
        return {"error": "Food already exists in directory"}, 400

    # Add to Database
    new_food = FoodDirectory(
        foodName=food_name,
        calories=calories,
        protein=protein,
        carbs=carbs,
        fat=fat,
        fiber=fiber
    )
    db.session.add(new_food)
    db.session.commit()

    # Add to foodData.json
    json_path = "foodData.json"
    new_item = {
        "foodName": food_name,
        "calories": calories,
        "protein": protein,
        "carbs": carbs,
        "fat": fat,
        "fiber": fiber
    }

    try:
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                food_list = json.load(f)
        else:
            food_list = []
        
        food_list.append(new_item)
        
        with open(json_path, "w") as f:
            json.dump(food_list, f, indent=4)
    except Exception as e:
        print(f"Error updating foodData.json: {str(e)}")
        # We don't fail the whole request if JSON update fails, but we should log it
        return {"success": True, "message": "Food added to DB, but failed to update JSON file.", "id": new_food.id}, 201

    return {"success": True, "message": "Food added to DB and JSON file successfully!", "id": new_food.id}, 201


@mealBp.route("/api/logs/logMeal", methods=["POST"])
@loginRequired
def logMeal():
    data = request.get_json()

    targetId = data.get("foodId")
    gramsEaten = data.get("amountInG")
    localDateStr = data.get("date")  # New: client can pass their local date

    foodItem = FoodDirectory.query.get(targetId)

    if not foodItem:
        return {"error": "Food ID not found in directory. Please add it first."}, 404

    macros = calculateSnapshotMacros(foodItem, gramsEaten)

    # Determine dateLogged
    if localDateStr:
        try:
            # Combine provided date with current UTC time to keep time precision
            # but ensure it falls on the correct day for the user
            clientDate = datetime.strptime(localDateStr, "%Y-%m-%d").date()
            currentTime = datetime.now(timezone.utc).time()
            dateLogged = datetime.combine(clientDate, currentTime)
        except Exception as e:
            dateLogged = datetime.now(timezone.utc)
    else:
        dateLogged = datetime.now(timezone.utc)

    newLog = FoodLog(
        userId=session["userId"],
        foodName=foodItem.foodName,
        amountInG=gramsEaten,
        calories=macros["calories"],
        protein=macros["protein"],
        carbs=macros["carbs"],
        fat=macros["fat"],
        fiber=macros["fiber"],
        dateLogged=dateLogged
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


@mealBp.route("/api/checkNewDay", methods=["GET"])
@loginRequired
def checkNewDay():
    # User sends their current local date (YYYY-MM-DD)
    localDateStr = request.args.get("date")
    if not localDateStr:
        return {"error": "Missing 'date' parameter"}, 400
    
    # Get the last logged meal for this user
    lastLog = (
        FoodLog.query.filter_by(userId=session["userId"])
        .order_by(FoodLog.dateLogged.desc())
        .first()
    )
    
    if not lastLog:
        # No logs ever, so we can treat it as same day/ready to log
        return {"newDay": False, "today": localDateStr}
    
    # Convert lastLog.dateLogged (UTC) to a date string for comparison
    # Ideally, we'd want to know the local date of that log, 
    # but for a "reset" check, simple UTC date works if the user is 
    # consistent. Better: just compare with the last known local date.
    
    # Let's get the date part of the last log
    lastLogDateStr = lastLog.dateLogged.date().isoformat()
    
    # If the provided current date is different from the last log date (UTC)
    # we can say it's a new day. This is a bit rough due to timezones,
    # but it fulfills the user's request for "diff from last meal date".
    isNewDay = localDateStr != lastLogDateStr
    
    return {
        "newDay": isNewDay,
        "lastLogDate": lastLogDateStr,
        "today": localDateStr
    }


@mealBp.route("/api/logs/today/totalNutriConsumed", methods=["GET"])
@loginRequired
def totalNutriConsumed():
    # Allow client to specify their local date
    localDateStr = request.args.get("date")
    
    if localDateStr:
        try:
            # localDateStr is expected in YYYY-MM-DD format
            todayDate = datetime.strptime(localDateStr, "%Y-%m-%d").date()
        except Exception as e:
            todayDate = datetime.now(timezone.utc).date()
    else:
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
        .filter(FoodLog.userId == session["userId"])
        .first()
    )

    hydration_stats = (
        db.session.query(func.sum(HydrationLog.amountMl).label("water"))
        .filter(func.date(HydrationLog.loggedAt) == todayDate)
        .filter(HydrationLog.userId == session["userId"])
        .first()
    )

    return {
        "calories": round(stats.calories or 0, 1),
        "protein": round(stats.protein or 0, 1),
        "carbs": round(stats.carbs or 0, 1),
        "fat": round(stats.fat or 0, 1),
        "fiber": round(stats.fiber or 0, 1),
        "water": hydration_stats.water or 0
    }


@mealBp.route("/api/logs/today/allLogs", methods=["GET"])
@loginRequired
def today():
    # Allow client to specify their local date
    localDateStr = request.args.get("date")
    
    if localDateStr:
        try:
            todayDate = datetime.strptime(localDateStr, "%Y-%m-%d").date()
        except Exception as e:
            todayDate = datetime.now(timezone.utc).date()
    else:
        todayDate = datetime.now(timezone.utc).date()

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


@mealBp.route("/api/logs/today/hydration")
@loginRequired
def getTodayHydration():
    todayDate = datetime.now(timezone.utc).date()
    logsForToday = (
        HydrationLog.query.filter(
            func.date(HydrationLog.loggedAt) == todayDate,
            HydrationLog.userId == session["userId"],
        )
        .order_by(HydrationLog.loggedAt.desc())
        .all()
    )

    totalAmount = sum(log.amountMl for log in logsForToday)

    output = []
    for log in logsForToday:
        output.append(
            {
                "id": log.id,
                "amountMl": log.amountMl,
                "beverageType": log.beverageType,
                "loggedAt": log.loggedAt.isoformat(),
            }
        )

    return {"total": totalAmount, "logs": output}


@mealBp.route("/api/logs/hydration", methods=["POST"])
@loginRequired
def logHydration():
    data = request.json
    amountMl = float(data.get("amountMl", 0))
    beverageType = data.get("beverageType", "Water")

    if amountMl <= 0:
        return {"error": "Invalid amount"}, 400

    newLog = HydrationLog(
        userId=session["userId"],
        amountMl=amountMl,
        beverageType=beverageType,
        loggedAt=datetime.now(timezone.utc),
    )

    db.session.add(newLog)
    db.session.commit()

    return {"message": "Hydration logged successfully", "id": newLog.id}, 201


@mealBp.route("/api/logs/today/deleteHydration/<id>", methods=["DELETE"])
@loginRequired
def deleteHydrationLog(id):
    logToDelete = HydrationLog.query.filter_by(id=id, userId=session["userId"]).first()

    if not logToDelete:
        return {"error": "Log not found"}, 404

    db.session.delete(logToDelete)
    db.session.commit()

    return {"message": "Log deleted successfully"}, 200


@mealBp.route("/api/gemini/recommendation", methods=["POST"])
@loginRequired
def getRecommendation():
    # Allow client to specify their local date
    localDateStr = request.args.get("date")
    
    if localDateStr:
        try:
            todayDate = datetime.strptime(localDateStr, "%Y-%m-%d").date()
        except Exception as e:
            todayDate = datetime.now(timezone.utc).date()
    else:
        todayDate = datetime.now(timezone.utc).date()

    import sys
    print(f"DEBUG: Recommendation for date: {todayDate}", file=sys.stderr)

    try:
        user = User.query.get(session["userId"])
             
        if not user:
             print("DEBUG: No user found in session!", file=sys.stderr)
             return {"error": "User not found"}, 401
             
        # Fetch today's totals
        stats = (
            db.session.query(
                func.sum(FoodLog.calories).label("calories"),
                func.sum(FoodLog.protein).label("protein"),
                func.sum(FoodLog.carbs).label("carbs"),
                func.sum(FoodLog.fat).label("fat"),
                func.sum(FoodLog.fiber).label("fiber"),
            )
            .filter(func.date(FoodLog.dateLogged) == todayDate)
            .filter(FoodLog.userId == user.id)
            .first()
        )
        totalConsumed = {
            "calories": round(stats.calories or 0, 1),
            "protein": round(stats.protein or 0, 1),
            "carbs": round(stats.carbs or 0, 1),
            "fat": round(stats.fat or 0, 1),
            "fiber": round(stats.fiber or 0, 1),
        }
        
        print(f"DEBUG: Total Consumed: {totalConsumed}", file=sys.stderr)

        # Fetch today's logs
        logsForToday = FoodLog.query.filter(
            func.date(FoodLog.dateLogged) == todayDate,
            FoodLog.userId == user.id,
        ).all()
        allLogs = [log.foodName for log in logsForToday]
        
        print(f"DEBUG: All Logs: {allLogs}", file=sys.stderr)

        userTargets = {
            "calories": user.targetCalories,
            "protein": user.targetProtein,
            "carbs": user.targetCarbs,
            "fat": user.targetFat,
            "fiber": user.targetFiber
        }

        systemPrompt = (
            "You are a helpful nutrition assistant for the NutriTracker app. Your goal is to analyze the user's daily food logs and provide personalized advice tailored to an Indian diet. "
            "Analyze the user's progress toward their daily goals (Calories, Protein, Carbs, Fat, Fiber) based on their consumed nutrients and targets. "
            "Suggest common natural Indian food sources to help them reach their goals. "
            "DO NOT recommend supplements or protein powders. If they have overeaten, suggest how to adjust. "
            "Keep the response very short, encouraging, and actionable (max 1-2 sentences). "
            "Use bullet points for the advice if possible. Do not use bold or italics formatting."
        )

        userPrompt = (
            f"Today I have consumed: {totalConsumed}. "
            f"My goals are: {userTargets}. "
            f"The foods I logged today: {allLogs}. "
            "Based on this, what's your advice for my next meal or my current progress?"
        )

        # Call local Ollama instead of Gemini
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3.2:3b",
            "prompt": f"System: {systemPrompt}\n\nUser: {userPrompt}",
            "stream": False
        }

        print(f"DEBUG: Ollama Prompt: {payload['prompt']}", file=sys.stderr)

        response = requests.post(url, json=payload)
        print(f"DEBUG: Ollama Status: {response.status_code}", file=sys.stderr)
        print(f"DEBUG: Ollama Response: {response.text}", file=sys.stderr)
        response.raise_for_status()
        result = response.json()
        
        advice = result.get('response', "Keep going! You're doing great.")
        return {"recommendation": advice.strip()}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"AI error: {str(e)}"}, 500


@mealBp.route("/api/logs/checkAvailability/<int:days>", methods=["GET"])
@loginRequired
def checkAvailability(days):
    # Count distinct dates in FoodLog for this user
    distinctDaysCount = (
        db.session.query(func.count(func.distinct(func.date(FoodLog.dateLogged))))
        .filter(FoodLog.userId == session["userId"])
        .scalar()
    )
    
    return {
        "available": distinctDaysCount >= days,
        "daysLogged": distinctDaysCount,
        "requiredDays": days
    }


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


@mealBp.route("/api/logs/hydration/checkAvailability/<int:days>")
@loginRequired
def checkHydrationAvailability(days):
    distinctDaysCount = (
        db.session.query(func.count(func.distinct(func.date(HydrationLog.loggedAt))))
        .filter(HydrationLog.userId == session["userId"])
        .scalar()
    )

    return {
        "available": distinctDaysCount >= 3,  # Limiter: need at least 3 days
        "daysLogged": distinctDaysCount,
        "requiredDays": 3
    }


@mealBp.route("/api/logs/hydration/avg/<int:days>", methods=["GET"])
@loginRequired
def sendHydrationAvg(days):
    todayDate = datetime.now(timezone.utc).date()
    
    # Get last X days of total water per day
    stats = (
        db.session.query(
            func.date(HydrationLog.loggedAt).label("date"),
            func.sum(HydrationLog.amountMl).label("total")
        )
        .filter(HydrationLog.userId == session["userId"])
        .filter(func.date(HydrationLog.loggedAt) < todayDate)
        .group_by(func.date(HydrationLog.loggedAt))
        .order_by(func.date(HydrationLog.loggedAt).desc())
        .limit(days)
        .all()
    )

    graphData = [float(s.total) for s in stats]
    avgWater = sum(graphData) / len(graphData) if graphData else 0

    return {
        "average": {
            "water": round(avgWater, 1)
        },
        "graphData": graphData,
        "daysFound": len(graphData)
    }


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
