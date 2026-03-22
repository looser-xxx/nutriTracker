# NutriTrack

A comprehensive nutrition and meal tracking application built with **Flask**, **SQLAlchemy**, and a modern **Vanilla JS** frontend.

## Features
- **Daily Tracking:** Log meals and track your calorie and macro intake.
- **Statistics Dashboard:** View weekly and monthly trends of your nutritional habits.
- **PWA Ready:** Install the app on your mobile device for easy access.
- **Dark Mode Support:** Modern UI that adapts to your system preferences.

## 📱 App Preview

| Home Screen | Today's Log | Statistics |
| :---: | :---: | :---: |
| ![Home](images/home.png) | ![Today's Log](images/todayLog.png) | ![Statistics](images/statistics.png) |

## Getting Started

Follow these instructions to set up and run the application on your local machine.

### Prerequisites
- Python 3.10 or higher

### Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/looser-xxx/nutriTracker.git
    cd nutriTracker
    ```
2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    ```
3.  **Activate the virtual environment:**
    - On Linux/macOS: `source venv/bin/activate`
    - On Windows: `venv\Scripts\activate`
4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application
1.  **Start the Flask server:**
    ```bash
    python3 app.py
    ```
2.  **Access the application:**
    The application will be running at `http://127.0.0.1:5000/`.

## 🐳 Running with Docker

The application is fully containerized and ready for production using **Docker** and **Docker Compose**.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Setup & Run
1.  **Configure Environment Variables:**
    Ensure you have a `.env` file in the root directory with the following:
    ```env
    SECRET_KEY=your_secret_key
    GOOGLE_CLIENT_ID=your_google_client_id
    GOOGLE_CLIENT_SECRET=your_google_client_secret
    OLLAMA_URL=http://host.docker.internal:11434  # To connect to Ollama on the host
    ```

2.  **Build and Start the Containers:**
    ```bash
    docker compose up -d --build
    ```

3.  **Access the Application:**
    The application will be running at `http://localhost:5050`.

### Data Persistence
- The SQLite database is stored in the `./instance` directory on your host machine, which is mapped to the container. Your data will persist even if the container is removed or updated.
- Food and exercise data are automatically initialized and synced from `foodData.json` and `exerciseData.json` on the first run.

### Advantages of the Docker Setup
- **Production Grade:** Uses Gunicorn with Gevent workers for better performance and concurrency.
- **Easy Deployment:** Ideal for home servers, NAS (like Synology/TrueNAS), or cloud VPS.
- **Cloudflare Ready:** Pre-configured with `ProxyFix` to work seamlessly behind Cloudflare Tunnels.

## API Endpoints

### Food Management
- `POST /api/dataBase/admin/addFood`: Admin tool to add items to the directory.
- `GET /api/dataBase/directory`: List all food items in the database.

### Meal Logging
- `POST /api/logs/logMeal`: Log a meal (expects `foodId` and `amountInG`).
- `GET /api/logs/nutritionConsumed/<int:id>`: Get detailed nutrition for a specific log entry.
- `DELETE /api/logs/today/delete/<int:id>`: Remove a meal log by its ID.

### Tracking & Statistics
- `GET /api/logs/today/allLogs`: Get a list of all meals consumed today.
- `GET /api/logs/today/totalNutriConsumed`: Get the sum of all nutrients consumed today (Calories, Protein, Carbs, Fat, Fiber).
- `GET /api/logs/avg/<int:days>`: Get average nutritional intake and graph data for the last *X* days (e.g., 7 for weekly, 30 for monthly).
