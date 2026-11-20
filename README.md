# PhishGuard – Phishing Website Prediction using URL

Run:  `pip install -r requirements.txt`  then  `python app.py`  → http://127.0.0.1:5000

* Paste your slideshow image links in `config.py` (SLIDES list). Slideshow plays once and stops on the last slide.
* `user_data.db` (sqlite3) is created automatically on first run (tables: users, predictions).
* Use the same scikit-learn version that created `model/model.pkl`.
