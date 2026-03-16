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

    const fetchTodayStats = async () => {
        try {
            const response = await fetch('/api/logs/today/totalNutriConsumed');
            if (!response.ok) throw new Error('Failed to fetch today stats');
            const data = await response.json();
            
            // Update todayMain card (showing Calories Left)
            if (todayMain) {
                const h1 = todayMain.querySelector('h1');
                const p = todayMain.querySelector('p');
                const dailyGoal = userTargets.calories; 
                
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
                            'valCalories': userTargets.calories,
                            'valProtein': userTargets.protein,
                            'valCarbs': userTargets.carbs,
                            'valFat': userTargets.fat,
                            'valFiber': userTargets.fiber
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
                const maxCal = Math.max(...graph, userTargets.calories);
                
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
                selectedFoodInput.value = food.name;
                selectedFoodInput.setAttribute('data-id', food.id);
                // Store full macros for display
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
    
    // Accordion Logic for Today's Meals
    if (todaysMealList) {
        todaysMealList.addEventListener('click', (e) => {
            const item = e.target.closest('.expandable');
            if (!item) return;

            const targetId = item.getAttribute('data-details');
            const targetDetails = document.getElementById(targetId);

            // Close all others
            const allItems = todaysMealList.querySelectorAll('.expandable');
            const allDetails = todaysMealList.querySelectorAll('.mealDetails');

            allItems.forEach(i => {
                if (i !== item) i.classList.remove('expanded');
            });
            allDetails.forEach(d => {
                if (d !== targetDetails) d.classList.add('hiddenView');
            });

            // Toggle current
            item.classList.toggle('expanded');
            targetDetails.classList.toggle('hiddenView');
        });
    }


    if (foodSearch) {
        const fetchAndFilter = async () => {
            console.log("FETCH TRIGGERED");
            const query = foodSearch.value.trim();
            
            if (query.length < 3) {
                foodListContainer.innerHTML = '';
                foodListContainer.classList.remove('active');
                clearSearchBtn.classList.add('hiddenView');
                return;
            }

            clearSearchBtn.classList.remove('hiddenView');

            // Debounce the search
            if (typingTimer) clearTimeout(typingTimer);
            
            typingTimer = setTimeout(async () => {
                console.log("Fetching results for:", query);
                try {
                    const res = await fetch(`/api/dataBase/directory?q=${encodeURIComponent(query)}`);
                    const data = await res.json();
                    console.log("Results found:", data.count);
                    renderFoodList(data.directory || []);
                } catch (e) {
                    console.error("Failed to fetch food list", e);
                }
            }, 300); // 300ms debounce
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
        if (!foodSearch.contains(e.target) && !foodListContainer.contains(e.target) && e.target !== clearSearchBtn) {
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

    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                playStatsAnimation();
            });
        });
    }

    if (todayMain) todayMain.addEventListener('click', () => toggleModal(modalNutrients, true));
    if (closeNutrientsBtn) closeNutrientsBtn.addEventListener('click', () => toggleModal(modalNutrients, false));
    if (modalNutrients) modalNutrients.addEventListener('click', (e) => { if (e.target === modalNutrients) toggleModal(modalNutrients, false); });

    if (navAdd) navAdd.addEventListener('click', () => toggleModal(addMealModal, true));
    if (closeAddMealBtn) closeAddMealBtn.addEventListener('click', () => toggleModal(addMealModal, false));
    if (addMealModal) addMealModal.addEventListener('click', (e) => { if (e.target === addMealModal) toggleModal(addMealModal, false); });

    if (navStats) navStats.addEventListener('click', () => toggleModal(statsContainer, true));
    if (closeStatsBtn) closeStatsBtn.addEventListener('click', () => toggleModal(statsContainer, false));

    if (navWorkout) navWorkout.addEventListener('click', () => toggleModal(workoutContainer, true));
    if (closeWorkoutBtn) closeWorkoutBtn.addEventListener('click', () => toggleModal(workoutContainer, false));

    // Today's Meals Toggle
    if (viewAllMealsBtn) viewAllMealsBtn.addEventListener('click', () => toggleModal(todaysMealsContainer, true));
    if (closeTodaysMealsBtn) closeTodaysMealsBtn.addEventListener('click', () => toggleModal(todaysMealsContainer, false));

    // Side Menu Toggle
    const menuBtn = document.getElementById('menuBtn');
    const menuOverlay = document.getElementById('menuOverlay');
    const closeMenuBtn = document.getElementById('closeMenu');
    
    // Profile Elements
    const profileMenuItem = document.querySelector('.menuList .menuItem:first-child');
    const profileContainer = document.getElementById('profileContainer');
    const closeProfileBtn = document.getElementById('closeProfile');

    const fetchAndRenderProfile = async () => {
        try {
            const res = await fetch('/api/profile');
            if (res.ok) {
                const data = await res.json();
                document.getElementById('profName').textContent = data.fullName || '-';
                document.getElementById('profUser').textContent = data.username || '-';
                document.getElementById('profSerial').textContent = data.serialNumber || '-';
                document.getElementById('profAge').textContent = data.age || '-';
                document.getElementById('profSex').textContent = data.sex || '-';
                document.getElementById('profHeight').textContent = data.height ? data.height + ' cm' : '-';
                document.getElementById('profWeight').textContent = data.weight ? data.weight + ' kg' : '-';
                document.getElementById('profBicep').textContent = data.bicepSize ? data.bicepSize + ' in' : '-';
            }
        } catch (err) {
            console.error("Error fetching profile:", err);
        }
    };

    if (profileMenuItem) {
        profileMenuItem.addEventListener('click', () => {
            toggleModal(menuOverlay, false);
            toggleModal(profileContainer, true);
            fetchAndRenderProfile();
        });
    }

    if (closeProfileBtn) {
        closeProfileBtn.addEventListener('click', () => toggleModal(profileContainer, false));
    }

    if (profileContainer) {
        profileContainer.addEventListener('click', (e) => {
            if (e.target === profileContainer) toggleModal(profileContainer, false);
        });
    }

    if (menuBtn) {
        menuBtn.addEventListener('click', () => toggleModal(menuOverlay, true));
    }

    if (closeMenuBtn) {
        closeMenuBtn.addEventListener('click', () => toggleModal(menuOverlay, false));
    }


    if (closeDbViewBtn) {
        closeDbViewBtn.addEventListener('click', () => toggleModal(dbViewContainer, false));
    }

    if (dbViewContainer) {
        dbViewContainer.addEventListener('click', (e) => {
            if (e.target === dbViewContainer) toggleModal(dbViewContainer, false);
        });
    }

    if (menuOverlay) {
        menuOverlay.addEventListener('click', (e) => {
            if (e.target === menuOverlay) {
                toggleModal(menuOverlay, false);
            }
        });
    }


    if (addMealForm) {
        addMealForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const foodName = selectedFoodInput.value;
            const foodId = selectedFoodInput.getAttribute('data-id');
            const amount = parseFloat(foodQuantity.value);
            
            if (!foodId || isNaN(amount) || amount <= 0) {
                alert("Please select a food and enter a valid quantity.");
                return;
            }

            const payload = {
                foodId: parseInt(foodId),
                amountInG: amount
            };

            try {
                const response = await fetch('/api/logs/logMeal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                const result = await response.json();
                
                if (response.status === 201 || result.message) {
                    toggleModal(addMealModal, false);
                    // Refresh data
                    fetchTodayStats();
                    renderHomeMealList();
                    // Reset form
                    foodSearch.value = '';
                    selectedFoodInput.value = '';
                    selectedFoodInput.removeAttribute('data-id');
                    foodQuantity.value = '100';
                    updateNutritionDisplay(null);
                    clearSearchBtn.classList.add('hiddenView');
                } else {
                    alert("Error adding meal: " + (result.error || result.message));
                }
            } catch (error) {
                console.error("Error submitting meal:", error);
                alert("Failed to add meal. See console.");
            }
        });
    }

    if (workoutForm) {
        workoutForm.addEventListener('submit', (e) => {
            e.preventDefault();
        });
    }

    // Theme Toggle
    const themeSwitch = document.getElementById('themeSwitch');
    
    // Check saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.documentElement.removeAttribute('data-theme');
        if (themeSwitch) themeSwitch.checked = false;
    } else {
        // Default to dark or use saved dark
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

    // Logout Handler
    const logoutItem = document.getElementById('logoutItem');
    if (logoutItem) {
        logoutItem.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/logout');
                const data = await res.json();
                if (data.success) {
                    window.location.href = data.redirect;
                }
            } catch (err) {
                console.error("Logout failed", err);
            }
        });
    }
});
