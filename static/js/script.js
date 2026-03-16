document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    let serverFoodDatabase = [];
    const todayMain = document.getElementById('todayMain');
    const modalNutrients = document.getElementById('modalNutrients');
    const closeNutrientsBtn = document.getElementById('closeNutrients');

    const navAdd = document.getElementById('navAdd');
    const addMealModal = document.getElementById('addMeal');
    const closeAddMealBtn = document.getElementById('closeAddMeal');
    const addMealForm = document.getElementById('addMealForm');

    // Stats Elements
    const navStats = document.getElementById('navStats');
    const statsContainer = document.getElementById('statsContainer');
    const closeStatsBtn = document.getElementById('closeStats');
    const tabBtns = document.querySelectorAll('.tabBtn');
    const chartBars = document.querySelectorAll('.bar');
    const goalFills = document.querySelectorAll('.goalFill');
    const countUpElements = document.querySelectorAll('.countUp');
    const insightText = document.getElementById('insightText');

    // Workout Elements
    const navWorkout = document.getElementById('navWorkout');
    const workoutContainer = document.getElementById('workoutContainer');
    const closeWorkoutBtn = document.getElementById('closeWorkout');
    const workoutForm = document.getElementById('workoutForm');

    // Today's Meals Elements
    const viewAllMealsBtn = document.getElementById('viewAllMealsBtn');
    const todaysMealsContainer = document.getElementById('todaysMealsContainer');
    const closeTodaysMealsBtn = document.getElementById('closeTodaysMeals');
    const todaysMealList = document.getElementById('todaysMealList');


    // Search Elements
    const foodSearch = document.getElementById('foodSearch');
    const clearSearchBtn = document.getElementById('clearSearch');
    const foodListContainer = document.getElementById('foodList');
    const selectedFoodInput = document.getElementById('selectedFood');

    // Stepper Elements
    const qtyDec = document.getElementById('qtyDec');
    const qtyInc = document.getElementById('qtyInc');
    const foodQuantity = document.getElementById('foodQuantity');

    // Nutrition Info Elements
    const infoCal = document.getElementById('infoCal');
    const infoPro = document.getElementById('infoPro');
    const infoCarb = document.getElementById('infoCarb');
    const infoFat = document.getElementById('infoFat');

    // View DB Elements
    const viewDbItem = document.getElementById('viewDbItem');
    const dbViewContainer = document.getElementById('dbViewContainer');
    const closeDbViewBtn = document.getElementById('closeDbView');
    const dbFoodList = document.getElementById('dbFoodList');

    // --- Mock Data ---
    const foodDatabase = [
        { name: "Apple", id: 101, macros: { cal: 52, p: 0.3, c: 14, f: 0.2, fib: 2.4 } },
        { name: "Banana", id: 102, macros: { cal: 89, p: 1.1, c: 23, f: 0.3, fib: 2.6 } },
        { name: "Chicken Breast", id: 103, macros: { cal: 165, p: 31, c: 0, f: 3.6, fib: 0 } },
        { name: "Egg (Boiled)", id: 104, macros: { cal: 155, p: 13, c: 1.1, f: 11, fib: 0 } },
        { name: "Oats", id: 105, macros: { cal: 389, p: 16.9, c: 66.3, f: 6.9, fib: 10.6 } },
        { name: "Rice (White)", id: 106, macros: { cal: 130, p: 2.7, c: 28, f: 0.3, fib: 0.4 } },
        { name: "Broccoli", id: 107, macros: { cal: 34, p: 2.8, c: 7, f: 0.4, fib: 2.6 } },
        { name: "Almonds", id: 108, macros: { cal: 579, p: 21, c: 22, f: 50, fib: 12.5 } },
        { name: "Salmon", id: 109, macros: { cal: 208, p: 20, c: 0, f: 13, fib: 0 } },
        { name: "Greek Yogurt", id: 110, macros: { cal: 59, p: 10, c: 3.6, f: 0.4, fib: 0 } }
    ];

    let typingTimer = null;

    // --- Helper Functions ---

    const fetchTodayStats = async () => {
        try {
            const response = await fetch('/api/logs/today/totalNutriConsumed');
            if (!response.ok) throw new Error('Failed to fetch today stats');
            const data = await response.json();
            
            // Update todayMain card (showing Calories Left)
            if (todayMain) {
                const h1 = todayMain.querySelector('h1');
                const p = todayMain.querySelector('p');
                const dailyGoal = 2500; // This could be dynamic later
                
                if (h1 && data.calories !== undefined) {
                    h1.classList.remove('skeleton'); 
                    h1.style.minWidth = '0';
                    const consumed = Math.round(data.calories);
                    const left = Math.max(0, dailyGoal - consumed);
                    
                    // Animate to the 'Left' value
                    animateValue(h1, 0, left, 1000);
                }
                if (p) {
                    p.textContent = `of ${dailyGoal.toLocaleString()} kcal goal`;
                }
            }
        } catch (error) {
            console.error('Error loading today stats:', error);
        }
    };

    const renderHomeMealList = async () => {
        const homeMealList = document.querySelector('.contentArea .mealList');
        if (!homeMealList) return;

        try {
            const response = await fetch('/api/logs/today/allLogs');
            if (!response.ok) throw new Error('Failed to fetch today meals');
            const data = await response.json();
            const meals = data.mealsConsumed || [];
            
            homeMealList.innerHTML = '';
            
            if (meals.length === 0) {
                homeMealList.innerHTML = '<li class="mealItem" style="justify-content: center;">No meals logged today.</li>';
                return;
            }

            // Show only last 4 meals
            const recentMeals = meals.slice(-4).reverse();

            recentMeals.forEach((meal, index) => {
                const li = document.createElement('li');
                li.className = 'mealItem animate-slide-down';
                li.style.animationDelay = `${index * 0.1}s`; // Stagger effect
                li.style.opacity = '0'; // Start invisible so animation handles fade-in
                
                li.innerHTML = `
                    <div class="mealInfo">
                        <span class="mealName">${meal.foodName}</span>
                        <span class="mealTime">${Math.round(meal.gramsEaten)}g</span>
                    </div>
                    <span class="mealCals">${Math.round(meal.calories)} kcal</span>
                `;
                homeMealList.appendChild(li);
            });
        } catch (error) {
            console.error('Error loading home meal list:', error);
        }
    };

    // Call immediately on load
    fetchTodayStats();
    renderHomeMealList();

