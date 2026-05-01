from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import hmac
import hashlib
import subprocess
import os
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

from database import (
    init_db,
    save_measurement,
    get_history,
    save_event,
    get_events
)

# ----------------------------
# INIT
# ----------------------------

app = Flask(__name__)
app.secret_key = "en-hemmelig-nøgle-123"

# Firebase
key_path = "/home/Ramsen0004/Eksamensprojekt-informatik/serviceAccountKey.json"
if not os.path.exists(key_path):
    key_path = r"C:\Users\ramse\Eksamensprojekt-informatik\serviceAccountKey.json"

cred = credentials.Certificate(key_path)
firebase_admin.initialize_app(cred)

# ----------------------------
# SYSTEM STATE
# ----------------------------

measurements = {
    "soil_moisture": 0,
    "temperature": 0,
    "humidity": 0,
    "nitrogen": 50,
    "phosphorus": 50,
    "potassium": 50
}

settings = {
    "min_soil_moisture": 45,
    "max_temperature": 30,
    "min_humidity": 50,
    "auto_watering": True,
}

pump_active = False

# ----------------------------
# SENSOR DATA (ESP32)
# ----------------------------

@app.route("/api/sensor", methods=["POST"])
def api_sensor():
    global measurements

    data = request.get_json()

    measurements["temperature"] = float(data.get("temperature", 0))
    measurements["humidity"] = float(data.get("humidity", 0))
    measurements["soil_moisture"] = float(data.get("soil_moisture", 0))

    # behold næringsstoffer
    measurements["nitrogen"] = measurements.get("nitrogen", 50)
    measurements["phosphorus"] = measurements.get("phosphorus", 50)
    measurements["potassium"] = measurements.get("potassium", 50)

    save_measurement(measurements)

    return jsonify({"status": "ok"})


# ----------------------------
# STATUS TIL ESP32
# ----------------------------

@app.route("/status")
def status():
    return jsonify({"pump": bool(pump_active)})

# ----------------------------
# LOGIN (uændret)
# ----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json()
        id_token = data.get("idToken")
        try:
            decoded = firebase_auth.verify_id_token(id_token)
            session["user"] = decoded["email"]
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# ----------------------------
# HOME (dashboard)
# ----------------------------

@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "home.html",
        data=measurements,
        settings=settings,
        pump_active=pump_active,
        alerts=build_alerts(),
        nutrient_advice=build_nutrient_advice(),
        system_status=system_status(build_alerts()),
        history=get_history()
    )


# ----------------------------
# API DATA (frontend graf)
# ----------------------------

@app.route("/api/data")
def api_data():
    return jsonify({
        "data": measurements,
        "pump_active": pump_active,
        "alerts": build_alerts(),
        "system_status": system_status(build_alerts()),
        "history": get_history(limit=20),
        "settings": settings,
        "auto_watering": settings["auto_watering"]
    })


# ----------------------------
# MANUEL STYRING (PUMPE)
# ----------------------------

@app.route("/water", methods=["POST"])
def water():
    global pump_active

    action = request.form.get("action")

    if action == "start":
        pump_active = True
        save_event("Pumpen startet manuelt")

    elif action == "stop":
        pump_active = False
        save_event("Pumpen stoppet manuelt")

    elif action == "toggle_auto":
        settings["auto_watering"] = not settings["auto_watering"]

    return redirect(url_for("home"))


# ----------------------------
# HISTORIK
# ----------------------------

@app.route("/history")
def history_page():
    return render_template(
        "history.html",
        history=get_history(),
        events=get_events()
    )


@app.route("/api/history")
def api_history():
    return jsonify({
        "history": get_history(limit=20),
        "events": get_events(limit=10)
    })


# ----------------------------
# GØDNING
# ----------------------------

@app.route("/fertilize", methods=["POST"])
def fertilize():
    nutrient = request.form.get("nutrient")
    dose = float(request.form.get("dose", 10))

    if nutrient in measurements:
        measurements[nutrient] = min(100, measurements[nutrient] + dose)
        save_event(f"Gødning tilsat: {nutrient} +{dose}")

    return redirect(url_for("home"))


# ----------------------------
# ALERT LOGIK
# ----------------------------

def build_alerts():
    alerts = []

    if measurements["soil_moisture"] < settings["min_soil_moisture"]:
        alerts.append("Lav jordfugtighed")

    if measurements["temperature"] > settings["max_temperature"]:
        alerts.append("For høj temperatur")

    if measurements["humidity"] < settings["min_humidity"]:
        alerts.append("Lav luftfugtighed")

    return alerts


def build_nutrient_advice():
    advice = []

    if measurements["nitrogen"] < 15:
        advice.append("Lav nitrogen")
    if measurements["phosphorus"] < 15:
        advice.append("Lav fosfor")
    if measurements["potassium"] < 15:
        advice.append("Lav kalium")

    return advice


def system_status(alerts):
    return "Advarsel" if alerts else "Normal"


# ----------------------------
# AUTO DEPLOY (GitHub)
# ----------------------------

WEBHOOK_SECRET = "Shekib"
REPO_PATH = "/home/Ramsen0004/Eksamensprojekt-informatik"
WSGI_PATH = "/var/www/ramsen0004_pythonanywhere_com_wsgi.py"


@app.route("/update_server", methods=["POST"])
def update_server():
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        return "No signature", 403

    sha_name, github_signature = signature.split("=")

    mac = hmac.new(
        WEBHOOK_SECRET.encode(),
        msg=request.data,
        digestmod=hashlib.sha256
    )

    if not hmac.compare_digest(mac.hexdigest(), github_signature):
        return "Bad signature", 403

    subprocess.check_call(["git", "-C", REPO_PATH, "pull"])
    subprocess.check_call(["touch", WSGI_PATH])

    return "Updated", 200


# ----------------------------
# START
# ----------------------------

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)