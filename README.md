# PhishGuard – Phishing Website Prediction Using URL

A machine learning project that detects phishing websites using the Random Forest algorithm. It analyses website URLs and domain features to identify suspicious links and help users browse the internet more safely.

## Features
- Phishing website prediction using URL features
- Random Forest machine learning algorithm
- Flask-based web application
- User registration and login
- Prediction history and dashboard

## Installation and Setup

1. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:

   ```bash
   python app.py
   ```

3. Open your browser and visit:

   http://127.0.0.1:5000

## Configuration
- Paste your slideshow image links in `config.py` (SLIDES list).
- The slideshow plays once and stops on the last slide.
- `user_data.db` (SQLite3) is created automatically on first run. It contains the users and predictions tables.
- Use the same scikit-learn version that created `model/model.pkl`.

## Technologies Used
- Python
- Flask
- Machine Learning
- Random Forest
- HTML, CSS and JavaScript
- SQLite3