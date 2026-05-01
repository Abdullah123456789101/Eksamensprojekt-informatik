from flask import Flask, render_template, request, redirect, url_for, jsonify
from fake_data import generate_measurements
import hmac
import hashlib
import subprocess
from auth import login_user
from flask import session
from firebase_admin import auth as firebase_auth
import firebase_admin
from firebase_admin import credentials
import os
from database import (
    init_db,
    save_measurement,
    get_history,
    save_event,
    get_events
)


key_path = "/home/Ramsen0004/Eksamensprojekt-informatik/serviceAccountKey.json"
if not os.path.exists(key_path):
    key_path = r"C:\Users\ramse\Eksamensprojekt-informatik\serviceAccountKey.json"

cred = credentials.Certificate(key_path)

app = Flask(__name__)
app.secret_key = "en-hemmelig-nøgle-123"

firebase_admin.initialize_app(cred)


# System state
measurements = {}
settings = {
    "min_soil_moisture": 45,
    "max_temperature": 30,
    "min_humidity": 50,
    "auto_watering": True,
}
pump_active = False


# SIMULATION

def update_measurements():
    global measurements, pump_active

    if not measurements:
        return

    # AUTO-VANDING LOGIK
    if settings["auto_watering"]:
        if measurements["soil_moisture"] < settings["min_soil_moisture"]:
            if not pump_active:
                pump_active = True
                save_event("Auto-vanding: Pumpe startet (lav jordfugtighed)")
        elif measurements["soil_moisture"] >= settings["min_soil_moisture"] + 10:
            if pump_active:
                pump_active = False
                save_event("Auto-vanding: Pumpe stoppet (fugtighed OK)")

    if pump_active:
        # Vand ON - fugtighed stiger
        measurements["soil_moisture"] += 2
        measurements["humidity"] += 1
        measurements["temperature"] -= 0.2

        # Planten bruger næring langsomt når den vandes
        measurements["nitrogen"] -= 0.2
        measurements["phosphorus"] -= 0.1
        measurements["potassium"] -= 0.1
    else:
        # Vand OFF - fugtighed falder
        measurements["soil_moisture"] -= 1
        measurements["humidity"] -= 0.5
        measurements["temperature"] += 0.1

        # Planten bruger næring
        measurements["nitrogen"] -= 0.05
        measurements["phosphorus"] -= 0.02
        measurements["potassium"] -= 0.02

    # Begræns værdier
    measurements["soil_moisture"] = max(0, min(100, measurements["soil_moisture"]))
    measurements["humidity"] = max(0, min(100, measurements["humidity"]))
    measurements["temperature"] = max(0, min(50, measurements["temperature"]))
    measurements["nitrogen"] = max(0, min(100, measurements["nitrogen"]))
    measurements["phosphorus"] = max(0, min(100, measurements["phosphorus"]))
    measurements["potassium"] = max(0, min(100, measurements["potassium"]))


# LOGIK

def build_alerts():
    alerts = []

    if measurements["soil_moisture"] < settings["min_soil_moisture"]:
        alerts.append("Jordfugtighed er under minimumsgrænsen - overvej at starte vanding.")
    if measurements["temperature"] > settings["max_temperature"]:
        alerts.append("Temperaturen er over maksimum - tjek ventilation.")
    if measurements["humidity"] < settings["min_humidity"]:
        alerts.append("Luftfugtighed er under minimumsgrænsen.")
    if measurements["nitrogen"] < 15:
        alerts.append("Lav nitrogen - tilsæt kvælstofgødning (f.eks. ammoniumnitrat).")
    if measurements["phosphorus"] < 15:
        alerts.append("Lav fosfor - tilsæt fosforgødning (f.eks. superfosfat).")
    if measurements["potassium"] < 15:
        alerts.append("Lav kalium - tilsæt kaliumgødning (f.eks. kaliumsulfat).")

    return alerts


def build_nutrient_advice():
    advice = []

    if measurements["nitrogen"] < 15:
        advice.append("Nitrogen under 15 - planten kan vise gule blade og langsom vækst.")
    if measurements["phosphorus"] < 15:
        advice.append("Fosfor under 15 - planten kan vise lilla/røde blade og dårlig rodvækst.")
    if measurements["potassium"] < 15:
        advice.append("Kalium under 15 - planten kan vise gule bladkanter og svage stængler.")

    return advice


def system_status(alerts):
    return "Advarsel" if alerts else "Normal"


# ROUTES

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

@app.route("/opret")
def opret():
    return render_template("opret.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    global measurements

    if not measurements:
        measurements = {
            "soil_moisture": 0,
            "temperature": 0,
            "humidity": 0,
            "nitrogen": 50,
            "phosphorus": 50,
            "potassium": 50
        }

    update_measurements()
    save_measurement(measurements)

    alerts = build_alerts()
    nutrient_advice = build_nutrient_advice()
    history = get_history()

    return render_template(
        "home.html",
        data=measurements,
        settings=settings,
        pump_active=pump_active,
        alerts=alerts,
        nutrient_advice=nutrient_advice,
        system_status=system_status(alerts),
        history=history
    )


@app.route("/api/data")
def api_data():
    global measurements

    if not measurements:
        measurements = {
            "soil_moisture": 0,
            "temperature": 0,
            "humidity": 0,
            "nitrogen": 50,
            "phosphorus": 50,
            "potassium": 50
        }

    update_measurements()
    save_measurement(measurements)

    alerts = build_alerts()
    history = get_history(limit=20)

    return jsonify({
        "data": {k: round(v, 1) for k, v in measurements.items()},
        "pump_active": pump_active,
        "alerts": alerts,
        "system_status": system_status(alerts),
        "history": history,
        "settings": settings,
        "auto_watering": settings["auto_watering"]
    })


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


@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    global settings

    if request.method == "POST":
        settings["min_soil_moisture"] = float(request.form.get("min_soil_moisture", 45))
        settings["max_temperature"] = float(request.form.get("max_temperature", 30))
        settings["min_humidity"] = float(request.form.get("min_humidity", 50))
        settings["auto_watering"] = request.form.get("auto_watering") == "on"

        save_event("Indstillinger blev opdateret")
        return redirect(url_for("settings_page"))

    return render_template("settings.html", settings=settings)


@app.route("/water", methods=["POST"])
def water():
    global pump_active

    action = request.form.get("action")

    if action == "start":
        pump_active = True
        save_event("Pumpen blev startet manuelt")
    elif action == "stop":
        pump_active = False
        save_event("Pumpen blev stoppet manuelt")
    elif action == "toggle_auto":
        settings["auto_watering"] = not settings["auto_watering"]
        status = "til" if settings["auto_watering"] else "fra"
        save_event(f"Auto-vanding blev slået {status}")

    return redirect(url_for("home"))


@app.route("/fertilize", methods=["POST"])
def fertilize():
    nutrient = request.form.get("nutrient")
    dose = float(request.form.get("dose", 10))

    nutrient_names = {
        "nitrogen": "Nitrogen (kvælstof)",
        "phosphorus": "Fosfor",
        "potassium": "Kalium"
    }

    if nutrient in measurements:
        measurements[nutrient] = min(100, measurements[nutrient] + dose)
        navn = nutrient_names.get(nutrient, nutrient)
        save_event(f"Gødning tilsat: {navn} +{dose:.0f} enheder (nu {measurements[nutrient]:.1f})")

    return redirect(url_for("home"))

# GITHUB AUTO-DEPLOY
WEBHOOK_SECRET = "Shekib"
REPO_PATH = "/home/Ramsen0004/Eksamensprojekt-informatik"
WSGI_PATH = "/var/www/ramsen0004_pythonanywhere_com_wsgi.py"


@app.route("/update_server", methods=["POST"])
def update_server():
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        return "No signature", 403

    try:
        sha_name, github_signature = signature.split("=", 1)
    except ValueError:
        return "Bad signature format", 403

    if sha_name != "sha256":
        return "Wrong hash type", 403

    mac = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        msg=request.data,
        digestmod=hashlib.sha256
    )

    if not hmac.compare_digest(mac.hexdigest(), github_signature):
        return "Signature mismatch", 403

    event = request.headers.get("X-GitHub-Event", "")
    if event != "push":
        return "Ignoring non-push event", 200

    try:
        subprocess.check_call(["git", "-C", REPO_PATH, "pull"])
        subprocess.check_call(["touch", WSGI_PATH])
        return "Updated successfully", 200
    except Exception as e:
        return f"Deploy error: {e}", 500
@app.route("/status")
def status():
    return jsonify({"pump": bool(pump_active)})
@app.route("/api/sensor", methods=["POST"])
def api_sensor():
    global measurements

    data = request.get_json()

    # Hvis measurements ikke findes endnu
    if not measurements:
        measurements = {}

    measurements["temperature"] = float(data.get("temperature", 0))
    measurements["humidity"] = float(data.get("humidity", 0))
    measurements["soil_moisture"] = float(data.get("soil_moisture", 0))

    # default værdier til gødning (du kan ændre senere)
    measurements["nitrogen"] = measurements.get("nitrogen", 50)
    measurements["phosphorus"] = measurements.get("phosphorus", 50)
    measurements["potassium"] = measurements.get("potassium", 50)

    # gem i database
    save_measurement(measurements)

    return jsonify({"status": "ok"})
# START APP

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)