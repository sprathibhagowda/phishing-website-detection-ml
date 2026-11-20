import json
import pickle
import sqlite3
import warnings
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse

import numpy as np
from flask import (Flask, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

import config
from feature import FeatureExtraction

warnings.filterwarnings("ignore")

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

with open("model/model.pkl", "rb") as f:
    gbc = pickle.load(f)

# Human friendly names + explanations for the 30 features (same order as the model)
FEATURE_INFO = {
    "UsingIp": ("IP address in URL", "URL uses a raw IP address instead of a domain name.", "URL"),
    "longUrl": ("URL length", "Very long URLs are often used to hide the real destination.", "URL"),
    "shortUrl": ("Shortening service", "Link goes through a URL shortener (bit.ly, tinyurl...).", "URL"),
    "symbol": ("'@' symbol", "An @ sign makes browsers ignore everything before it.", "URL"),
    "redirecting": ("'//' redirect", "A second // inside the URL can silently redirect you.", "URL"),
    "prefixSuffix": ("Hyphen in domain", "Phishers add '-' to imitate real brands (pay-pal.com).", "URL"),
    "SubDomains": ("Sub-domains", "Too many dots / sub-domains is a common obfuscation trick.", "URL"),
    "Hppts": ("HTTPS protocol", "Whether the site uses an encrypted HTTPS connection.", "URL"),
    "DomainRegLen": ("Domain registration length", "Phishing domains are usually registered for under a year.", "Domain"),
    "Favicon": ("Favicon source", "Favicon loaded from an external domain is suspicious.", "Page"),
    "NonStdPort": ("Non-standard port", "Uncommon ports can indicate a hidden server.", "URL"),
    "HTTPSDomainURL": ("'https' in domain name", "Fake 'https' word placed in the domain to look secure.", "URL"),
    "RequestURL": ("External objects", "Share of images/media loaded from other domains.", "Page"),
    "AnchorURL": ("Anchor links", "Share of <a> links pointing to other domains.", "Page"),
    "LinksInScriptTags": ("Links in meta/script tags", "Share of scripts and link tags loaded externally.", "Page"),
    "ServerFormHandler": ("Form handler", "Blank or off-site form actions can steal submitted data.", "Page"),
    "InfoEmail": ("Submits to email", "Page uses mail() / mailto: to send information.", "Page"),
    "AbnormalURL": ("Abnormal URL", "Host name does not match the registered identity.", "Domain"),
    "WebsiteForwarding": ("Redirect count", "Many automatic redirects hide the final page.", "Page"),
    "StatusBarCust": ("Status-bar tampering", "onMouseOver scripts that fake the link shown in the status bar.", "Page"),
    "DisableRightClick": ("Right-click disabled", "Blocking right-click stops users inspecting the page.", "Page"),
    "UsingPopupWindow": ("Pop-up windows", "Pop-ups asking for information are a classic phishing tactic.", "Page"),
    "IframeRedirection": ("Invisible iframes", "Hidden frames can load content from another site.", "Page"),
    "AgeofDomain": ("Domain age", "Young domains (under 6 months) are riskier.", "Domain"),
    "DNSRecording": ("DNS record", "Missing WHOIS/DNS record for the domain.", "Domain"),
    "WebsiteTraffic": ("Website traffic", "Popular sites rank well; phishing sites rarely do.", "Reputation"),
    "PageRank": ("Page rank", "Low page rank means the site is not well referenced.", "Reputation"),
    "GoogleIndex": ("Google indexed", "Legitimate sites are usually indexed by search engines.", "Reputation"),
    "LinksPointingToPage": ("Inbound links", "Few or no links pointing to the page.", "Reputation"),
    "StatsReport": ("Blacklist report", "Page appears in phishing statistics reports.", "Reputation"),
}


# ----------------------------------------------------------- database
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(config.DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(config.DATABASE)
    db.execute("""CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    mobile TEXT, email TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    db.execute("""CREATE TABLE IF NOT EXISTS predictions(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    safe_pct REAL NOT NULL,
                    phish_pct REAL NOT NULL,
                    features TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id))""")
    db.commit()
    db.close()


init_db()


def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if "user_id" not in session:
            flash("Please sign in to continue.", "warn")
            return redirect(url_for("login"))
        return view(*a, **kw)
    return wrapped


# ------------------------------------------------------------- helpers
def normalize_url(raw):
    """Accept links typed with or without a scheme."""
    raw = raw.strip()
    if not urlparse(raw).scheme or "://" not in raw:
        raw = "http://" + raw.lstrip("/")
    return raw


def build_feature_rows(details):
    rows = []
    for key, val in details.items():
        label, desc, group = FEATURE_INFO.get(key, (key, "", "Other"))
        status = {1: "safe", 0: "warn", -1: "risk"}.get(int(val), "warn")
        rows.append({"key": key, "label": label, "desc": desc, "group": group,
                     "value": int(val), "status": status})
    return rows


def pretty_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return s


app.jinja_env.filters["pretty_date"] = pretty_date


# -------------------------------------------------------------- routes
@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", slides=config.SLIDES,
                           slide_seconds=config.SLIDE_SECONDS)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        mobile = request.form["phone"].strip()
        pwd = request.form["password"]
        if len(name) < 3 or len(pwd) < 4:
            flash("Username needs 3+ characters and password 4+ characters.", "error")
            return render_template("register.html")
        db = get_db()
        try:
            db.execute("INSERT INTO users(name,password,mobile,email) VALUES (?,?,?,?)",
                       (name, generate_password_hash(pwd), mobile, email))
            db.commit()
        except sqlite3.IntegrityError:
            flash("That username is already taken.", "error")
            return render_template("register.html")
        flash("Account created! You can sign in now.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form["name"].strip()
        pwd = request.form["password"]
        user = get_db().execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
        if user and check_password_hash(user["password"], pwd):
            session.clear()
            session["user_id"], session["user_name"] = user["id"], user["name"]
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    rows = get_db().execute(
        "SELECT * FROM predictions WHERE user_id=? ORDER BY id DESC",
        (session["user_id"],)).fetchall()
    total = len(rows)
    phishing = sum(1 for r in rows if r["verdict"] == "phishing")
    return render_template("dashboard.html", rows=rows, total=total,
                           phishing=phishing, safe=total - phishing)


@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    if request.method == "POST":
        raw = request.form.get("url", "").strip()
        if not raw:
            flash("Please enter a URL.", "error")
            return render_template("predict.html")
        url = normalize_url(raw)
        try:
            obj = FeatureExtraction(url)
            x = np.array(obj.getFeaturesList()).reshape(1, 30)
            details = obj.getFeatureDetails()
            proba = gbc.predict_proba(x)[0]
            classes = list(gbc.classes_)
            p_safe = float(proba[classes.index(1)])
            p_phish = float(proba[classes.index(-1)])
        except Exception as e:
            flash(f"Could not analyse that URL ({e}).", "error")
            return render_template("predict.html")

        verdict = "safe" if p_safe >= p_phish else "phishing"
        db = get_db()
        cur = db.execute(
            "INSERT INTO predictions(user_id,url,verdict,safe_pct,phish_pct,features,created_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (session["user_id"], raw, verdict, round(p_safe * 100, 2),
             round(p_phish * 100, 2), json.dumps(details),
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        db.commit()
        return redirect(url_for("result", pid=cur.lastrowid))
    return render_template("predict.html")


@app.route("/result/<int:pid>")
@login_required
def result(pid):
    row = get_db().execute("SELECT * FROM predictions WHERE id=? AND user_id=?",
                           (pid, session["user_id"])).fetchone()
    if not row:
        flash("Prediction not found.", "error")
        return redirect(url_for("dashboard"))
    feats = build_feature_rows(json.loads(row["features"]))
    counts = {s: sum(1 for f in feats if f["status"] == s) for s in ("safe", "warn", "risk")}
    return render_template("result.html", p=row, feats=feats, counts=counts)


@app.route("/delete/<int:pid>", methods=["POST"])
@login_required
def delete(pid):
    db = get_db()
    db.execute("DELETE FROM predictions WHERE id=? AND user_id=?", (pid, session["user_id"]))
    db.commit()
    flash(f"Prediction #{pid} deleted.", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
