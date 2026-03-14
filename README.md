# NutriTrack

A simple nutrition and meal tracking application built with Flask and SQLAlchemy.

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
    - On Linux/macOS:
      ```bash
      source venv/bin/activate
      ```
    - On Windows:
      ```bash
      venv\Scripts\activate
      ```

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

## API Endpoints

- `POST /api/admin/addFood`: Add a new food item to the directory.
- `GET /api/directory`: List all food items in the directory.
- `POST /api/logMeal`: Log a meal with a specific food item and amount.
- `GET /api/nutritionConsumed/<id>`: Get calculated nutrition for a specific meal log.
- `GET /api/today`: Get a summary of all meals and nutrition consumed today.
