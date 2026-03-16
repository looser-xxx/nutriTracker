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

    const fetchAndRenderDb = async () => {
        try {
            const response = await fetch('/api/dataBase/directory');
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
            const response = await fetch('/api/logs/today/allLogs');
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
                    </div>
                `;
                todaysMealList.appendChild(li);
            });
        } catch (error) {
            console.error('Error loading today meals:', error);
            todaysMealList.innerHTML = '<li class="mealItem">Error loading meals.</li>';
        }
    };

    const toggleModal = (modal, show) => {
        if (show) {
            modal.classList.remove('hiddenView');
            // Trigger specific actions when opening
            if (modal === statsContainer) {
                playStatsAnimation();
            }
            if (modal === dbViewContainer) {
                fetchAndRenderDb();
            }
            if (modal === todaysMealsContainer) {
                fetchAndRenderTodayMeals();
            }
            if (modal === modalNutrients) {
                // Fetch real daily stats
                fetch('/api/logs/today/totalNutriConsumed')
                    .then(res => res.json())
                    .then(data => {
                        const targets = {
                            'valCalories': Math.round(data.calories || 0),
                            'valProtein': Math.round(data.protein || 0),
                            'valCarbs': Math.round(data.carbs || 0),
                            'valFat': Math.round(data.fat || 0),
                            'valFiber': Math.round(data.fiber || 0)
                        };
                        
                        // Hardcoded goals matching HTML text (could be dynamic later)
                        const goals = {
                            'valCalories': 2500,
                            'valProtein': 180,
                            'valCarbs': 300,
                            'valFat': 80,
                            'valFiber': 35
                        };

                        // Reset bars first
                        Object.keys(targets).forEach(id => {
                            const fillId = id.replace('val', 'fill');
                            const fillEl = document.getElementById(fillId);
                            if(fillEl) fillEl.style.width = '0%';
                        });

                        setTimeout(() => {
                            Object.keys(targets).forEach(id => {
                                // Animate Number
                                const el = document.getElementById(id);
                                if (el) {
                                    animateValue(el, 0, targets[id], 1000);
                                }
                                
                                // Animate Bar
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
            }
        } else {
            modal.classList.add('hiddenView');
            // Reset animations when closing to allow re-play
            if (modal === statsContainer) {
                resetStatsAnimation();
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
        
        // Find active tab
        const activeTab = document.querySelector('.tabBtn.active').getAttribute('data-tab');
        const apiUrl = activeTab === 'monthly' ? '/api/logs/avg/30' : '/api/logs/avg/7';
        const chartPlaceholder = document.querySelector('.chartPlaceholder');

        try {
            const response = await fetch(apiUrl);
            const data = await response.json();
            const avg = data.average;
            const graph = data.graphData;

            setTimeout(() => {
                // Clear and Update Graph Bars
                chartPlaceholder.innerHTML = '';
                const maxCal = Math.max(...graph, 2500);
                
                graph.forEach((val) => {
                    const bar = document.createElement('div');
                    bar.className = 'bar';
                    const height = (val / maxCal) * 100;
                    bar.style.height = `${Math.max(height, 5)}%`;
                    // Adjust width based on number of bars
                    bar.style.width = activeTab === 'monthly' ? '2%' : '10%';
                    chartPlaceholder.appendChild(bar);
                    
                    // Trigger animation
                    setTimeout(() => bar.classList.add('animate'), 10);
                });

                // Update Progress Bars & Numbers in Avg Section
                const goals = { calories: 2500, protein: 180, carbs: 300, fat: 80 };
                const goalItems = document.querySelectorAll('.avgSection .goalItem');
                goalItems.forEach(item => {
                    const label = item.querySelector('.goalLabel').textContent.toLowerCase();
                    if (avg[label] !== undefined) {
                        const countUp = item.querySelector('.countUp');
                        const fill = item.querySelector('.goalFill');
                        
                        animateValue(countUp, 0, Math.round(avg[label]), 1000);
                        const pct = Math.min((avg[label] / goals[label]) * 100, 100);
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
        element.innerHTML = '';
        let i = 0;
        
        // Add cursor
        const cursor = document.createElement('span');
        cursor.className = 'cursor';
        
        const type = () => {
            if (i < text.length) {
                // Insert text before the cursor
                element.innerHTML = text.substring(0, i + 1);
                element.appendChild(cursor);
                i++;
                typingTimer = setTimeout(type, speed);
            }
        };
        
        type();
    };


    const updateNutritionDisplay = (macros) => {
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
