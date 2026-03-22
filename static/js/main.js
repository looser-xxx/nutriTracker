document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    let serverFoodDatabase = [];
    let userTargets = { calories: 2500, protein: 150, carbs: 300, fat: 80, fiber: 30 };
    
    const todayMain = document.getElementById('todayMain');
    const modalNutrients = document.getElementById('modalNutrients');
    const closeNutrientsBtn = document.getElementById('closeNutrients');

    const navAdd = document.getElementById('navAdd');
    const addMealModal = document.getElementById('addMeal');
    const closeAddMealBtn = document.getElementById('closeAddMeal');
    const addMealForm = document.getElementById('addMealForm');

    // Hydration Elements
    const currentWaterText = document.getElementById('currentWater');
    const goalWaterText = document.getElementById('goalWater');
    const hydrationList = document.getElementById('hydrationList');
    const addHydrationModal = document.getElementById('addHydration');
    const addHydrationForm = document.getElementById('addHydrationForm');
    const closeAddHydrationBtn = document.getElementById('closeAddHydration');
    const waterAmountInput = document.getElementById('waterAmount');
    const waterDecBtn = document.getElementById('waterDec');
    const waterIncBtn = document.getElementById('waterInc');
    const beverageTypeSelect = document.getElementById('beverageType');

    const waterAction1 = document.getElementById('waterAction1'); // Quick Log
    const waterAction2 = document.getElementById('waterAction2'); // Custom Log

    const todaysHydrationContainer = document.getElementById('todaysHydrationContainer');
    const closeTodaysHydrationBtn = document.getElementById('closeTodaysHydration');
    const todaysHydrationList = document.getElementById('todaysHydrationList');

    const goalInputs = {
        calories: document.getElementById('goalEditCal'),
        protein: document.getElementById('goalEditPro'),
        carbs: document.getElementById('goalEditCar'),
        fat: document.getElementById('goalEditFat'),
        fiber: document.getElementById('goalEditFib'),
        water: document.getElementById('goalEditWater')
    };

    let typingTimer = null;
    let lastFetchedDate = null;

    // --- Helper Functions ---

    const fetchHydrationData = async () => {
        try {
            const [targetsRes, logsRes] = await Promise.all([
                fetch('/api/user/targets'),
                fetch('/api/logs/today/hydration')
            ]);
            
            const targets = await targetsRes.json();
            const logs = await logsRes.json();

            if (goalWaterText) goalWaterText.textContent = targets.water || 3000;
            if (currentWaterText) {
                currentWaterText.classList.remove('skeleton');
                animateValue(currentWaterText, 0, logs.total || 0, 1000);
            }

            const summaryP = (todayMain && window.location.pathname === '/hydration-new') ? todayMain.querySelector('p') : null;
            if (summaryP) {
                summaryP.innerHTML = `of <span id="goalWater">${targets.water || 3000}</span> ml goal`;
            }

            if (hydrationList) {
                renderHydrationLogs(logs.logs, hydrationList);
            }
            if (todaysHydrationList) {
                renderHydrationLogs(logs.logs, todaysHydrationList);
            }
        } catch (err) {
            console.error('Error fetching hydration data:', err);
        }
    };

    const renderHydrationLogs = (logs, container) => {
        if (!container) return;
        container.innerHTML = '';
        
        if (logs.length === 0) {
            container.innerHTML = '<li class="mealItem" style="justify-content: center; color: var(--text-muted);">No hydration logged today</li>';
            return;
        }

        logs.forEach(log => {
            const li = document.createElement('li');
            li.className = 'mealItem';
            li.innerHTML = `
                <div class="mealInfo">
                    <span class="mealName">${log.beverageType}</span>
                    <span class="mealTime">${new Date(log.loggedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span class="mealCals">${log.amountMl}ml</span>
                    <button class="deleteHydrationBtn deleteMealBtn" data-id="${log.id}">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 6h18"></path>
                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                        </svg>
                        <span>Delete</span>
                    </button>
                </div>
            `;
            container.appendChild(li);
        });

        // Add delete listeners
        container.querySelectorAll('.deleteHydrationBtn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                const isConfirming = btn.classList.contains('confirming');

                if (!isConfirming) {
                    btn.classList.add('confirming');
                    const span = btn.querySelector('span');
                    if (span) span.textContent = 'Confirm?';

                    setTimeout(() => {
                        if (btn.classList.contains('confirming')) {
                            btn.classList.remove('confirming');
                            if (span) span.textContent = 'Delete';
                        }
                    }, 3000);
                    return;
                }

                try {
                    btn.disabled = true;
                    btn.style.opacity = '0.5';
                    const res = await fetch(`/api/logs/today/deleteHydration/${id}`, { method: 'DELETE' });
                    if (res.ok) fetchHydrationData();
                } catch (err) {
                    console.error('Error deleting hydration log:', err);
                    btn.disabled = false;
                    btn.style.opacity = '1';
                }
            });
        });
    };

    const logHydration = async (amountMl, beverageType = 'Water') => {
        try {
            const res = await fetch('/api/logs/hydration', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amountMl, beverageType })
            });
            if (res.ok) {
                fetchHydrationData();
                if (addHydrationModal) addHydrationModal.classList.add('hiddenView');
            }
        } catch (err) {
            console.error('Error logging hydration:', err);
        }
    };

    const populateGoalInputs = () => {
        if (goalInputs.calories) goalInputs.calories.value = userTargets.calories;
        if (goalInputs.protein) goalInputs.protein.value = userTargets.protein;
        if (goalInputs.carbs) goalInputs.carbs.value = userTargets.carbs;
        if (goalInputs.fat) goalInputs.fat.value = userTargets.fat;
        if (goalInputs.fiber) goalInputs.fiber.value = userTargets.fiber;
        if (goalInputs.water) goalInputs.water.value = userTargets.water || 3000;
    };

    const getLocalDate = () => {
        const d = new Date();
        const date = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
        return date;
    };

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
    const motivationQuote = document.getElementById('motivationQuote');
    const quotes = [
        "Believe you can and you're halfway there.",
        "Your only limit is you.",
        "Don't stop until you're proud.",
        "Healthy is a way of life.",
        "Everything you need is already inside you.",
        "The only bad workout is the one that didn't happen.",
        "Fitness is not about being better than someone else. It's about being better than you were yesterday.",
        "Take care of your body. It's the only place you have to live.",
        "Fuel your body, feed your soul.",
        "Success starts with self-discipline."
    ];

    const waterQuotes = [
        "Water is the driving force of all nature.",
        "Stay hydrated, stay healthy!",
        "Drink more water. Your skin, your hair, your mind and your body will thank you.",
        "Pure water is the world's first and foremost medicine.",
        "A thirsty body is a tired body. Drink up!",
        "Keep calm and drink water.",
        "Hydration is the key to energy.",
        "Water: The original energy drink.",
        "Don't wait until you're thirsty to drink water.",
        "Your body is about 60% water. Be good to it."
    ];

    if (motivationQuote) {
        if (window.location.pathname === '/hydration') {
            const randomQuote = waterQuotes[Math.floor(Math.random() * waterQuotes.length)];
            motivationQuote.textContent = `"${randomQuote}"`;
        } else {
            const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
            motivationQuote.textContent = `"${randomQuote}"`;
        }
    }

    const todaysMealsContainer = document.getElementById('todaysMealsContainer');
    const closeTodaysMealsBtn = document.getElementById('closeTodaysMeals');
    const todaysMealList = document.getElementById('todaysMealList');

    // Hydration Stats Elements
    const waterStatsBtn = document.getElementById('waterStatsBtn');
    const hydrationStatsContainer = document.getElementById('hydrationStatsContainer');
    const closeHydrationStatsBtn = document.getElementById('closeHydrationStats');
    const hydrationInsightText = document.getElementById('hydrationInsightText');
    const avgWaterVal = document.getElementById('avgWaterVal');
    const avgWaterFill = document.getElementById('avgWaterFill');
    const statGoalWater = document.getElementById('statGoalWater');

    // --- Helper Functions ---

    const resetHydrationStatsAnimation = () => {
        const statsModal = document.getElementById('hydrationStatsContainer');
        if (!statsModal) return;
        const fills = statsModal.querySelectorAll('.goalFill');
        const countUps = statsModal.querySelectorAll('.countUp');
        fills.forEach(f => f.style.width = '0%');
        countUps.forEach(c => c.textContent = '0');
        if (hydrationInsightText) hydrationInsightText.innerHTML = '';
    };

    const playHydrationStatsAnimation = async () => {
        resetHydrationStatsAnimation();
        
        const statsModal = document.getElementById('hydrationStatsContainer');
        if (!statsModal) return;

        const activeTab = statsModal.querySelector('.tabBtn.active').getAttribute('data-tab');
        const days = activeTab === 'monthly' ? 30 : 7;
        const apiUrl = `/api/logs/hydration/avg/${days}`;
        const availabilityUrl = `/api/logs/hydration/checkAvailability/${days}`;
        
        const chartSection = statsModal.querySelector('.chartSection');
        const avgSection = statsModal.querySelector('.avgSection');
        const chartPlaceholder = statsModal.querySelector('.chartPlaceholder');

        if (chartSection) chartSection.classList.remove('stats-disabled');
        if (avgSection) avgSection.classList.remove('stats-disabled');
        if (hydrationInsightText) hydrationInsightText.innerHTML = 'Analyzing your hydration patterns...';

        try {
            const availabilityRes = await fetch(availabilityUrl);
            const availabilityData = await availabilityRes.json();

            if (!availabilityData.available) {
                if (chartSection) chartSection.classList.add('stats-disabled');
                if (avgSection) avgSection.classList.add('stats-disabled');
                
                const logged = availabilityData.daysLogged || 0;
                const required = availabilityData.requiredDays || 3;
                
                const msg = `<strong>Not enough data yet.</strong><br>You have logged water for ${logged} out of the ${required} days needed to generate ${activeTab} statistics. Keep logging!`;
                if (hydrationInsightText) hydrationInsightText.innerHTML = msg;
                return;
            }

            const response = await fetch(apiUrl);
            const data = await response.json();
            const avg = data.average.water;
            const graph = data.graphData;

            setTimeout(() => {
                if (chartPlaceholder) {
                    chartPlaceholder.innerHTML = '';
                    const goal = userTargets.water || 3000;
                    const maxWater = Math.max(...graph, goal);
                    
                    graph.forEach((val) => {
                        const bar = document.createElement('div');
                        bar.className = 'bar';
                        bar.style.backgroundColor = '#3498db'; // Water blue
                        const height = (val / maxWater) * 100;
                        bar.style.height = `${height}%`;
                        bar.style.width = activeTab === 'monthly' ? '2%' : '10%';
                        chartPlaceholder.appendChild(bar);
                        setTimeout(() => bar.classList.add('animate'), 10);
                    });
                }

                if (avgWaterVal) {
                    animateValue(avgWaterVal, 0, Math.round(avg), 1000);
                }
                if (statGoalWater) {
                    statGoalWater.textContent = userTargets.water || 3000;
                }
                if (avgWaterFill) {
                    const goal = userTargets.water || 3000;
                    const pct = Math.min((avg / goal) * 100, 100);
                    avgWaterFill.style.width = `${pct}%`;
                }

                const daysMsg = `${data.daysFound} logged days`;
                const insight = `Based on your ${activeTab} data (${daysMsg}), you're averaging ${Math.round(avg)}ml of water daily. ${avg >= (userTargets.water || 3000) ? "Excellent hydration levels!" : "Try to drink a bit more water consistently."}`;
                typeWriter(insight, hydrationInsightText, 30);
            }, 50);

        } catch (error) {
            console.error("Error loading hydration stats:", error);
        }
    };

    const dbViewContainer = document.getElementById('dbViewContainer');
    const closeDbViewBtn = document.getElementById('closeDbView');
    const dbFoodList = document.getElementById('dbFoodList');

    const profileMenuItem = document.getElementById('menuProfile') || document.querySelector('.menuList .menuItem:first-child');
    const menuGoals = document.getElementById('menuGoals') || document.querySelector('.menuList .menuItem:nth-child(2)');
    
    const profileContainer = document.getElementById('profileContainer');
    const closeProfileBtn = document.getElementById('closeProfile');

    const userGoalsModal = document.getElementById('userGoalsModal');
    const saveGoalsBtn = document.getElementById('saveGoals');
    const closeGoalsBtn = document.getElementById('closeGoals');

    const fetchUserTargets = async () => {
        try {
            const response = await fetch('/api/user/targets');
            if (response.ok) {
                userTargets = await response.json();
            }
        } catch (error) {
            console.error('Error fetching user targets:', error);
        }
    };

    const refreshDashboard = async () => {
        await fetchUserTargets();
        await fetchTodayStats();
        await renderHomeMealList();
    };

    window.changeVal = (id, delta) => {
        const input = document.getElementById(id);
        if (input) {
            const val = parseInt(input.value) || 0;
            input.value = Math.max(0, val + delta);
        }
    };

    const fetchTodayStats = async () => {
        try {
            const date = getLocalDate();
            const response = await fetch(`/api/logs/today/totalNutriConsumed?date=${date}`);
            if (!response.ok) throw new Error('Failed to fetch today stats');
            const data = await response.json();
            
            if (todayMain && window.location.pathname === '/') {
                const h1 = todayMain.querySelector('h1');
                const p = todayMain.querySelector('p');
                const dailyGoal = userTargets.calories;

                if (h1 && data.calories !== undefined) {
                    h1.classList.remove('skeleton');
                    h1.style.minWidth = '0';
                    const consumed = Math.round(data.calories);
                    const left = Math.max(0, dailyGoal - consumed);

                    animateValue(h1, 0, left, 1000);
                }
                if (p) {
                    p.textContent = `of ${dailyGoal.toLocaleString()} kcal goal`;
                }
            }            return data;
        } catch (error) {
            console.error('Error loading today stats:', error);
        }
    };

    const fetchAIAdvice = async () => {
        if (!motivationQuote || window.location.pathname === '/hydration') return;

        try {
            const date = getLocalDate();
            // Using /api/gemini/recommendation as seen in routeMeals.py
            const aiRes = await fetch(`/api/gemini/recommendation?date=${date}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (aiRes.ok) {
                const result = await aiRes.json();
                if (result.recommendation) {
                    typeWriter(`"${result.recommendation}"`, motivationQuote, 40);
                }
            } else if (aiRes.status === 429) {
                const result = await aiRes.json();
                if (result.recommendation) {
                    typeWriter(`"${result.recommendation}"`, motivationQuote, 40);
                }
            }
        } catch (error) {
            console.error('Error fetching AI advice:', error);
        }
    };

    const renderHomeMealList = async () => {
        const homeMealList = document.querySelector('.contentArea .mealList');
        if (!homeMealList) return;

        try {
            const date = getLocalDate();
            const response = await fetch(`/api/logs/today/allLogs?date=${date}`);
            if (!response.ok) throw new Error('Failed to fetch today meals');
            const data = await response.json();
            const meals = data.mealsConsumed || [];
            
            // If server confirms a different date than what we last had, it's a new day
            // Or if lastFetchedDate was null (initial load)
            if (lastFetchedDate && data.date !== lastFetchedDate) {
                console.log("Date changed, refreshing stats and advice...");
                fetchTodayStats();
                fetchAIAdvice();
            } else if (!lastFetchedDate) {
                // Initial load: fetch advice once
                fetchAIAdvice();
            }
            lastFetchedDate = data.date;

            homeMealList.innerHTML = '';
            
            if (meals.length === 0) {
                homeMealList.innerHTML = '<li class="mealItem" style="justify-content: center;">No meals logged today.</li>';
                return;
            }

            const recentMeals = meals.slice(-4).reverse();

            recentMeals.forEach((meal, index) => {
                const li = document.createElement('li');
                li.className = 'mealItem animate-slide-down';
                li.style.animationDelay = `${index * 0.1}s`;
                li.style.opacity = '0';
                
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

    const checkNewDay = () => {
        const currentDate = getLocalDate();
        // If lastFetchedDate is set and doesn't match current local date, it's a new day
        if (lastFetchedDate && currentDate !== lastFetchedDate) {
            console.log("New day detected by heartbeat. Refreshing...");
            refreshDashboard();
        }
    };

    // Heartbeat to check for date changes every 5 minutes
    setInterval(checkNewDay, 5 * 60 * 1000);

    fetchUserTargets().then(() => {
        fetchTodayStats();
        renderHomeMealList();
    });

    const fetchAndRenderDb = async () => {
        try {
            const response = await fetch('/api/dataBase/directory?q=all');
            if (!response.ok) throw new Error('Failed to fetch food data');
            const data = await response.json();
            const foodItems = data.directory || [];
            
            dbFoodList.innerHTML = '';
            
            if (foodItems.length === 0) {
                const li = document.createElement('li');
                li.className = 'mealItem';
                li.style.justifyContent = 'center';
                li.textContent = 'Database is empty.';
                dbFoodList.appendChild(li);
                return;
            }

            foodItems.forEach(food => {
                const li = document.createElement('li');
                li.className = 'mealItem';
                li.style.flexDirection = 'column';
                li.style.alignItems = 'flex-start';
                li.style.gap = '10px';
                
                li.innerHTML = `
                    <div style="width: 100%; display: flex; justify-content: space-between; align-items: center;">
                        <span class="mealName" style="font-size: 1.1rem;">${food.name}</span>
                        <span class="mealCals">${Math.round(food.macros.cal)} kcal</span>
                    </div>
                    <div class="miniNutrientGrid" style="width: 100%; justify-content: space-between; padding-top: 10px; border-top: 1px solid var(--border-color);">
                        <div class="miniItem"><span class="lbl">Pro</span><span class="val">${food.macros.p}g</span></div>
                        <div class="miniItem"><span class="lbl">Carb</span><span class="val">${food.macros.c}g</span></div>
                        <div class="miniItem"><span class="lbl">Fat</span><span class="val">${food.macros.f}g</span></div>
                        <div class="miniItem"><span class="lbl">Fib</span><span class="val">${food.macros.fib}g</span></div>
                    </div>
                `;
                dbFoodList.appendChild(li);
            });
            
        } catch (error) {
            console.error('Error loading food DB:', error);
            dbFoodList.innerHTML = '<li class="mealItem">Error loading data.</li>';
        }
    };

    const fetchAndRenderTodayMeals = async () => {
        try {
            const date = getLocalDate();
            const response = await fetch(`/api/logs/today/allLogs?date=${date}`);
            if (!response.ok) throw new Error('Failed to fetch today meals');
            const data = await response.json();
            const meals = data.mealsConsumed || [];
            
            todaysMealList.innerHTML = '';
            
            if (meals.length === 0) {
                todaysMealList.innerHTML = '<li class="mealItem" style="justify-content: center;">No meals logged today.</li>';
                return;
            }

            meals.forEach((meal, index) => {
                const detailsId = `details-${meal.logId}`;
                const li = document.createElement('li');
                li.innerHTML = `
                    <div class="mealItem expandable" data-details="${detailsId}">
                        <div class="mealInfo">
                            <span class="mealName">${meal.foodName}</span>
                        </div>
                        <span class="mealCals">${Math.round(meal.gramsEaten)}g</span>
                    </div>
                    <div id="${detailsId}" class="mealDetails hiddenView">
                        <div class="detailGrid">
                            <div class="detailItem"><span class="dLabel">Calories</span><span class="dVal">${Math.round(meal.calories)}</span></div>
                            <div class="detailItem"><span class="dLabel">Protein</span><span class="dVal">${meal.protein}g</span></div>
                            <div class="detailItem"><span class="dLabel">Carbs</span><span class="dVal">${meal.carbs}g</span></div>
                            <div class="detailItem"><span class="dLabel">Fat</span><span class="dVal">${meal.fat}g</span></div>
                            <div class="detailItem"><span class="dLabel">Fiber</span><span class="dVal">${meal.fiber}g</span></div>
                        </div>
                        <div class="detailActions">
                            <button class="deleteMealBtn" onclick="deleteMeal(${meal.logId}, this)">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M3 6h18"></path>
                                    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                                    <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                                </svg>
                                <span>Delete Log</span>
                            </button>
                        </div>
                    </div>
                `;
                todaysMealList.appendChild(li);
            });
        } catch (error) {
            console.error('Error loading today meals:', error);
            todaysMealList.innerHTML = '<li class="mealItem">Error loading meals.</li>';
        }
    };

    window.deleteMeal = async (logId, btn) => {
        const isConfirming = btn.classList.contains('confirming');
        
        if (!isConfirming) {
            btn.classList.add('confirming');
            const span = btn.querySelector('span');
            if (span) span.textContent = 'Confirm?';
            
            setTimeout(() => {
                if (btn.classList.contains('confirming')) {
                    btn.classList.remove('confirming');
                    if (span) span.textContent = 'Delete Log';
                }
            }, 3000);
            return;
        }

        try {
            btn.disabled = true;
            btn.style.opacity = '0.5';
            const response = await fetch(`/api/logs/today/delete/${logId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                fetchTodayStats();
                fetchAndRenderTodayMeals();
                renderHomeMealList();
                fetchAIAdvice();
            } else {
                alert('Failed to delete log.');
                btn.disabled = false;
                btn.style.opacity = '1';
            }
        } catch (error) {
            console.error('Error deleting meal:', error);
            btn.disabled = false;
            btn.style.opacity = '1';
        }
    };

    const toggleModal = (modal, show) => {
        if (!modal) return;
        if (show) {
            modal.classList.remove('hiddenView');
            if (statsContainer && modal === statsContainer) playStatsAnimation();
            if (hydrationStatsContainer && modal === hydrationStatsContainer) playHydrationStatsAnimation();
            if (dbViewContainer && modal === dbViewContainer) fetchAndRenderDb();
            if (todaysMealsContainer && modal === todaysMealsContainer) fetchAndRenderTodayMeals();
            if (modalNutrients && modal === modalNutrients) {
                fetchUserTargets().then(() => {
                    const date = getLocalDate();
                    fetch(`/api/logs/today/totalNutriConsumed?date=${date}`)
                        .then(res => res.json())
                        .then(data => {
                        const targets = {
                            'valCalories': Math.round(data.calories || 0),
                            'valProtein': Math.round(data.protein || 0),
                            'valCarbs': Math.round(data.carbs || 0),
                            'valFat': Math.round(data.fat || 0),
                            'valFiber': Math.round(data.fiber || 0)
                        };
                        
                        const goals = {
                            'valCalories': userTargets.calories,
                            'valProtein': userTargets.protein,
                            'valCarbs': userTargets.carbs,
                            'valFat': userTargets.fat,
                            'valFiber': userTargets.fiber
                        };
                        
                        Object.keys(goals).forEach(id => {
                            const goalId = id.replace('val', 'goal');
                            const goalEl = document.getElementById(goalId);
                            if (goalEl) goalEl.textContent = goals[id];
                        });

                        Object.keys(targets).forEach(id => {
                            const fillId = id.replace('val', 'fill');
                            const fillEl = document.getElementById(fillId);
                            if(fillEl) fillEl.style.width = '0%';
                        });

                        setTimeout(() => {
                            Object.keys(targets).forEach(id => {
                                const el = document.getElementById(id);
                                if (el) animateValue(el, 0, targets[id], 1000);
                                
                                const fillId = id.replace('val', 'fill');
                                const fillEl = document.getElementById(fillId);
                                if (fillEl) {
                                    const pct = Math.min((targets[id] / goals[id]) * 100, 100);
                                    fillEl.style.width = pct + '%';
                                }
                            });
                        }, 50);
                    })
                    .catch(err => console.error('Error fetching nutrients for modal:', err));
                });
            }
        } else {
            modal.classList.add('hiddenView');
            if (statsContainer && modal === statsContainer) {
                resetStatsAnimation();
                const chartSection = statsContainer.querySelector('.chartSection');
                const avgSection = statsContainer.querySelector('.avgSection');
                const insightText = document.getElementById('insightText');
                if (chartSection) chartSection.classList.remove('stats-disabled');
                if (avgSection) avgSection.classList.remove('stats-disabled');
                if (insightText) insightText.innerHTML = 'Analyzing your patterns...';
            }
        }
    };

    // --- Animation Logic ---

    const resetStatsAnimation = () => {
        chartBars.forEach(bar => {
            bar.classList.remove('animate');
            void bar.offsetWidth; 
        });
        goalFills.forEach(fill => {
            fill.style.width = '0%';
        });
        countUpElements.forEach(el => {
            el.textContent = '0';
        });
        if (typingTimer) clearTimeout(typingTimer);
        insightText.innerHTML = '';
    };

    const playStatsAnimation = async () => {
        resetStatsAnimation();
        
        const activeTab = document.querySelector('.tabBtn.active').getAttribute('data-tab');
        const days = activeTab === 'monthly' ? 30 : 7;
        const apiUrl = `/api/logs/avg/${days}`;
        const availabilityUrl = `/api/logs/checkAvailability/${days}`;
        
        const statsModal = document.getElementById('statsContainer');
        if (!statsModal) return;

        const chartSection = statsModal.querySelector('.chartSection');
        const avgSection = statsModal.querySelector('.avgSection');
        const insightText = document.getElementById('insightText');
        const chartPlaceholder = statsModal.querySelector('.chartPlaceholder');

        // Reset states
        if (chartSection) chartSection.classList.remove('stats-disabled');
        if (avgSection) avgSection.classList.remove('stats-disabled');
        if (insightText) insightText.innerHTML = 'Analyzing your patterns...';

        try {
            // Check availability
            const availabilityRes = await fetch(availabilityUrl);
            const availabilityData = await availabilityRes.json();

            if (!availabilityData.available) {
                if (chartSection) chartSection.classList.add('stats-disabled');
                if (avgSection) avgSection.classList.add('stats-disabled');
                
                const logged = availabilityData.daysLogged !== undefined ? availabilityData.daysLogged : 0;
                const required = availabilityData.requiredDays !== undefined ? availabilityData.requiredDays : days;
                
                const msg = `<strong>Not enough data yet.</strong><br>You have logged food for ${logged} out of the ${required} days needed to generate ${activeTab} statistics. Keep logging!`;
                if (insightText) insightText.innerHTML = msg;
                return;
            }

            const response = await fetch(apiUrl);
            const data = await response.json();
            const avg = data.average;
            const graph = data.graphData;

            setTimeout(() => {
                if (chartPlaceholder) {
                    chartPlaceholder.innerHTML = '';
                    const maxCal = Math.max(...graph, userTargets.calories);
                    
                    graph.forEach((val) => {
                        const bar = document.createElement('div');
                        bar.className = 'bar';
                        const height = (val / maxCal) * 100;
                        bar.style.height = `${height}%`;
                        bar.style.width = activeTab === 'monthly' ? '2%' : '10%';
                        chartPlaceholder.appendChild(bar);
                        setTimeout(() => bar.classList.add('animate'), 10);
                    });
                }

                const goals = { 
                    calories: userTargets.calories, 
                    protein: userTargets.protein, 
                    carbs: userTargets.carbs, 
                    fat: userTargets.fat 
                };
                const goalItems = document.querySelectorAll('.avgSection .goalItem');
                goalItems.forEach(item => {
                    const label = item.querySelector('.goalLabel').textContent.toLowerCase();
                    if (avg[label] !== undefined) {
                        const goalNumbers = item.querySelector('.goalNumbers');
                        const unit = label === 'calories' ? '' : 'g';
                        goalNumbers.innerHTML = `<span class="countUp">0</span> / ${goals[label]}${unit}`;
                        
                        const newCountUp = item.querySelector('.countUp');
                        animateValue(newCountUp, 0, Math.round(avg[label]), 1000);
                        
                        const pct = Math.min((avg[label] / goals[label]) * 100, 100);
                        const fill = item.querySelector('.goalFill');
                        fill.style.width = `${pct}%`;
                    }
                });

                const daysMsg = `${data.daysFound} logged days`;
                const mockInsight = `Based on your ${activeTab} data (${daysMsg}), you're averaging ${Math.round(avg.calories)} calories. ${avg.calories < 2000 ? "You're consistently in a deficit." : "You're meeting your maintenance goals."}`;
                typeWriter(mockInsight, insightText, 30);
            }, 50);

        } catch (error) {
            console.error("Error loading stats:", error);
        }
    };

    const animateValue = (obj, start, end, duration) => {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start).toLocaleString();
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    };

    const typeWriter = (text, element, speed) => {
        if (typingTimer) clearTimeout(typingTimer);
        element.innerHTML = '';
        let i = 0;
        const cursor = document.createElement('span');
        cursor.className = 'cursor';
        
        const type = () => {
            if (i < text.length) {
                element.innerHTML = text.substring(0, i + 1);
                element.appendChild(cursor);
                i++;
                typingTimer = setTimeout(type, speed);
            } else {
                // Remove cursor after finishing
                const c = element.querySelector('.cursor');
                if (c) c.remove();
            }
        };
        type();
    };


    const renderFoodList = (foods) => {
        foodListContainer.innerHTML = '';
        if (foods.length === 0) {
            const noResult = document.createElement('div');
            noResult.className = 'foodOption';
            noResult.style.cursor = 'default';
            noResult.style.color = '#999';
            noResult.textContent = 'No results found';
            foodListContainer.appendChild(noResult);
            return;
        }
        foods.sort((a, b) => a.name.localeCompare(b.name));
        foods.forEach(food => {
            const div = document.createElement('div');
            div.className = 'foodOption';
            div.textContent = food.name;
            if (food.name === selectedFoodInput.value) div.classList.add('selected');
            div.addEventListener('click', () => {
                selectedFoodInput.value = food.name;
                selectedFoodInput.setAttribute('data-id', food.id);
                selectedFoodInput.setAttribute('data-nutrients', JSON.stringify(food.macros));
                
                foodSearch.value = food.name;
                updateNutritionDisplay(food.macros);
                foodListContainer.classList.remove('active');
                clearSearchBtn.classList.remove('hiddenView');
            });
            foodListContainer.appendChild(div);
        });
        foodListContainer.classList.add('active');
    };

    // --- Event Listeners ---
    
    if (todaysMealList) {
        todaysMealList.addEventListener('click', (e) => {
            const item = e.target.closest('.expandable');
            if (!item) return;

            const targetId = item.getAttribute('data-details');
            const targetDetails = document.getElementById(targetId);

            const allItems = todaysMealList.querySelectorAll('.expandable');
            const allDetails = todaysMealList.querySelectorAll('.mealDetails');

            allItems.forEach(i => { if (i !== item) i.classList.remove('expanded'); });
            allDetails.forEach(d => { if (d !== targetDetails) d.classList.add('hiddenView'); });

            item.classList.toggle('expanded');
            targetDetails.classList.toggle('hiddenView');
        });
    }


    if (foodSearch) {
        const fetchAndFilter = async () => {
            const query = foodSearch.value.trim();
            if (query.length < 3) {
                foodListContainer.innerHTML = '';
                foodListContainer.classList.remove('active');
                clearSearchBtn.classList.add('hiddenView');
                return;
            }

            clearSearchBtn.classList.remove('hiddenView');
            if (typingTimer) clearTimeout(typingTimer);
            
            typingTimer = setTimeout(async () => {
                try {
                    const res = await fetch(`/api/dataBase/directory?q=${encodeURIComponent(query)}`);
                    const data = await res.json();
                    renderFoodList(data.directory || []);
                } catch (e) {
                    console.error("Failed to fetch food list", e);
                }
            }, 300);
        };
        foodSearch.addEventListener('input', fetchAndFilter);
        foodSearch.addEventListener('focus', fetchAndFilter);
        foodSearch.addEventListener('click', fetchAndFilter);
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', () => {
            foodSearch.value = '';
            selectedFoodInput.value = '';
            clearSearchBtn.classList.add('hiddenView');
            updateNutritionDisplay(null);
            foodListContainer.innerHTML = '';
            foodListContainer.classList.remove('active');
            foodSearch.focus();
        });
    }

    document.addEventListener('click', (e) => {
        if (foodSearch && !foodSearch.contains(e.target) && !foodListContainer.contains(e.target) && e.target !== clearSearchBtn) {
            foodListContainer.classList.remove('active');
        }
    });

    if (qtyDec && qtyInc && foodQuantity) {
        qtyDec.addEventListener('click', () => {
            let currentVal = parseInt(foodQuantity.value) || 0;
            if (currentVal > 0) foodQuantity.value = Math.max(0, currentVal - 10);
        });
        qtyInc.addEventListener('click', () => {
            let currentVal = parseInt(foodQuantity.value) || 0;
            foodQuantity.value = currentVal + 10;
        });
    }

    const updateNutritionDisplay = (macros) => {
        if (!infoCal || !infoPro || !infoCarb || !infoFat) return;
        if (!macros) {
            infoCal.textContent = '-';
            infoPro.textContent = '-';
            infoCarb.textContent = '-';
            infoFat.textContent = '-';
            return;
        }
        infoCal.textContent = Math.round(macros.cal || 0);
        infoPro.textContent = (macros.p || 0) + 'g';
        infoCarb.textContent = (macros.c || 0) + 'g';
        infoFat.textContent = (macros.f || 0) + 'g';
    };

    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                playStatsAnimation();
            });
        });
    }

    // --- Event Listeners ---

    if (waterAction1) {
        waterAction1.addEventListener('click', () => logHydration(250, 'Water'));
    }

    if (waterAction2) {
        waterAction2.addEventListener('click', () => toggleModal(addHydrationModal, true));
    }

    if (closeAddHydrationBtn) {
        closeAddHydrationBtn.addEventListener('click', () => toggleModal(addHydrationModal, false));
    }

    if (addHydrationModal) {
        addHydrationModal.addEventListener('click', (e) => {
            if (e.target === addHydrationModal) toggleModal(addHydrationModal, false);
        });
    }

    if (addHydrationForm) {
        addHydrationForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const amount = parseFloat(waterAmountInput.value);
            const type = beverageTypeSelect.value;
            logHydration(amount, type);
        });
    }

    if (waterDecBtn && waterAmountInput) {
        waterDecBtn.addEventListener('click', () => {
            waterAmountInput.value = Math.max(0, parseInt(waterAmountInput.value) - 50);
        });
    }

    if (waterIncBtn && waterAmountInput) {
        waterIncBtn.addEventListener('click', () => {
            waterAmountInput.value = parseInt(waterAmountInput.value) + 50;
        });
    }

    if (closeTodaysHydrationBtn) {
        closeTodaysHydrationBtn.addEventListener('click', () => toggleModal(todaysHydrationContainer, false));
    }

    if (todaysHydrationContainer) {
        todaysHydrationContainer.addEventListener('click', (e) => {
            if (e.target === todaysHydrationContainer) toggleModal(todaysHydrationContainer, false);
        });
    }

    if (todayMain) {
        todayMain.addEventListener('click', () => {
            if (window.location.pathname === '/hydration') {
                toggleModal(todaysHydrationContainer, true);
            } else {
                toggleModal(modalNutrients, true);
            }
        });
    }

    if (closeNutrientsBtn) closeNutrientsBtn.addEventListener('click', () => toggleModal(modalNutrients, false));
    if (modalNutrients) modalNutrients.addEventListener('click', (e) => { if (e.target === modalNutrients) toggleModal(modalNutrients, false); });

    if (navAdd) {
        navAdd.addEventListener('click', () => {
            if (window.location.pathname === '/hydration') {
                toggleModal(addHydrationModal, true);
            } else {
                toggleModal(addMealModal, true);
            }
        });
    }

    if (closeAddMealBtn) closeAddMealBtn.addEventListener('click', () => toggleModal(addMealModal, false));
    if (addMealModal) addMealModal.addEventListener('click', (e) => { if (e.target === addMealModal) toggleModal(addMealModal, false); });

    const action2Btn = document.getElementById('action2Btn');
    if (action2Btn) action2Btn.addEventListener('click', () => toggleModal(statsContainer, true));
    if (closeStatsBtn) closeStatsBtn.addEventListener('click', () => toggleModal(statsContainer, false));

    if (waterStatsBtn) {
        waterStatsBtn.addEventListener('click', () => toggleModal(hydrationStatsContainer, true));
    }
    if (closeHydrationStatsBtn) {
        closeHydrationStatsBtn.addEventListener('click', () => toggleModal(hydrationStatsContainer, false));
    }

    if (hydrationStatsContainer) {
        const hStatsTabs = hydrationStatsContainer.querySelectorAll('.tabBtn');
        hStatsTabs.forEach(btn => {
            btn.addEventListener('click', () => {
                hStatsTabs.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                playHydrationStatsAnimation();
            });
        });
    }

    // if (navWorkout) navWorkout.addEventListener('click', () => toggleModal(workoutContainer, true));
    if (closeWorkoutBtn) closeWorkoutBtn.addEventListener('click', () => toggleModal(workoutContainer, false));

    const action1Btn = document.getElementById('action1Btn');
    if (action1Btn) action1Btn.addEventListener('click', () => toggleModal(todaysMealsContainer, true));
    if (closeTodaysMealsBtn) closeTodaysMealsBtn.addEventListener('click', () => toggleModal(todaysMealsContainer, false));

    const menuBtn = document.getElementById('menuBtn');
    const menuOverlay = document.getElementById('menuOverlay');
    const closeMenuBtn = document.getElementById('closeMenu');

    const fetchAndRenderProfile = async () => {
        try {
            const res = await fetch('/api/profile');
            if (res.ok) {
                const data = await res.json();
                document.getElementById('profName').textContent = data.fullName || '-';
                document.getElementById('profUser').textContent = data.username || '-';
                document.getElementById('profSerial').textContent = data.serialNumber || '-';
                document.getElementById('profAge').textContent = data.age || '-';
                document.getElementById('profSex').textContent = data.gender || '-';
                document.getElementById('profHeight').textContent = data.height ? data.height + ' cm' : '-';
                document.getElementById('profWeight').textContent = data.weight ? data.weight + ' kg' : '-';
                document.getElementById('profBicep').textContent = data.bicepSize ? data.bicepSize + ' in' : '-';
            }
        } catch (err) {
            console.error("Error fetching profile:", err);
        }
    };

    if (profileMenuItem) {
        profileMenuItem.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleModal(menuOverlay, false);
            toggleModal(profileContainer, true);
            fetchAndRenderProfile();
        });
    }

    if (menuGoals) {
        menuGoals.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleModal(menuOverlay, false);
            populateGoalInputs();
            toggleModal(userGoalsModal, true);
        });
    }

    if (saveGoalsBtn) {
        saveGoalsBtn.addEventListener('click', async () => {
            const newTargets = {
                calories: goalInputs.calories ? parseInt(goalInputs.calories.value) : userTargets.calories,
                protein: goalInputs.protein ? parseInt(goalInputs.protein.value) : userTargets.protein,
                carbs: goalInputs.carbs ? parseInt(goalInputs.carbs.value) : userTargets.carbs,
                fat: goalInputs.fat ? parseInt(goalInputs.fat.value) : userTargets.fat,
                fiber: goalInputs.fiber ? parseInt(goalInputs.fiber.value) : userTargets.fiber,
                water: goalInputs.water ? parseInt(goalInputs.water.value) : (userTargets.water || 3000)
            };

            try {
                const res = await fetch('/api/user/targets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newTargets)
                });
                
                if (res.ok) {
                    await fetchUserTargets();
                    if (window.location.pathname === '/hydration') {
                        fetchHydrationData();
                    } else {
                        fetchTodayStats();
                    }
                    toggleModal(userGoalsModal, false);
                    
                    // Show a quick success feedback if possible, or just close
                    console.log('Goals updated successfully');
                } else {
                    alert('Failed to save goals.');
                }
            } catch (err) {
                console.error('Error saving goals:', err);
            }
        });
    }

    if (closeGoalsBtn) closeGoalsBtn.addEventListener('click', () => toggleModal(userGoalsModal, false));
    if (userGoalsModal) userGoalsModal.addEventListener('click', (e) => { if (e.target === userGoalsModal) toggleModal(userGoalsModal, false); });
    if (closeProfileBtn) closeProfileBtn.addEventListener('click', () => toggleModal(profileContainer, false));
    if (profileContainer) profileContainer.addEventListener('click', (e) => { if (e.target === profileContainer) toggleModal(profileContainer, false); });

    if (menuBtn) menuBtn.addEventListener('click', () => toggleModal(menuOverlay, true));
    if (closeMenuBtn) closeMenuBtn.addEventListener('click', () => toggleModal(menuOverlay, false));
    if (closeDbViewBtn) closeDbViewBtn.addEventListener('click', () => toggleModal(dbViewContainer, false));
    if (dbViewContainer) dbViewContainer.addEventListener('click', (e) => { if (e.target === dbViewContainer) toggleModal(dbViewContainer, false); });

    if (menuOverlay) {
        menuOverlay.addEventListener('mousedown', (e) => {
            if (e.target === menuOverlay) toggleModal(menuOverlay, false);
        });
    }


    if (addMealForm) {
        addMealForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const foodId = selectedFoodInput.getAttribute('data-id');
            const amount = parseFloat(foodQuantity.value);
            
            if (!foodId || isNaN(amount) || amount <= 0) {
                alert("Please select a food and enter a valid quantity.");
                return;
            }

            const payload = {
                foodId: parseInt(foodId),
                amountInG: amount,
                date: getLocalDate()
            };

            try {
                const response = await fetch('/api/logs/logMeal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.status === 201) {
                    toggleModal(addMealModal, false);
                    fetchTodayStats();
                    renderHomeMealList();
                    fetchAIAdvice();
                    foodSearch.value = '';
                    selectedFoodInput.value = '';
                    selectedFoodInput.removeAttribute('data-id');
                    foodQuantity.value = '100';
                    updateNutritionDisplay(null);
                    clearSearchBtn.classList.add('hiddenView');
                } else {
                    const result = await response.json();
                    alert("Error adding meal: " + (result.error || result.message));
                }
            } catch (error) {
                console.error("Error submitting meal:", error);
            }
        });
    }

    if (workoutForm) workoutForm.addEventListener('submit', (e) => e.preventDefault());

    // Theme Toggle
    const themeSwitch = document.getElementById('themeSwitch');
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.documentElement.removeAttribute('data-theme');
        if (themeSwitch) themeSwitch.checked = false;
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        if (themeSwitch) themeSwitch.checked = true;
    }

    if (themeSwitch) {
        themeSwitch.addEventListener('change', (e) => {
            if (e.target.checked) {
                document.documentElement.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
            }
        });
    }

    const logoutItem = document.getElementById('logoutItem');
    if (logoutItem) {
        logoutItem.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/logout');
                const data = await res.json();
                if (data.success) window.location.href = data.redirect;
            } catch (err) {
                console.error("Logout failed", err);
            }
        });
    }

    // Initialize page
    fetchUserTargets().then(() => {
        if (window.location.pathname === '/hydration') {
            fetchHydrationData();
        } else if (window.location.pathname === '/') {
            fetchTodayStats();
            renderHomeMealList();
            fetchAIAdvice();
        }
    });
});
