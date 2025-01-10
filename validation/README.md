# Flask API Application

This is a simple Flask API application that provides a web interface and API endpoints for validation.


## Installation

1. Clone this repository:
   ```
   git clone https://github.com/SocialTensor/VanaTensorValidation.git
   cd VanaTensorValidation
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask application:
   ```
   python app.py
   ```

2. Open a web browser and navigate to `http://localhost:5000` to see the web interface.

3. Use the following API endpoints:
   - GET `/status`: Check the API status
   - POST `/validate`: Validate data (send a JSON payload in the request body)

## API Endpoints

### GET /status

Returns the current status of the API.

**Response:**

