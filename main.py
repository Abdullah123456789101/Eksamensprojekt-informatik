from flask import Flask, render_template, request, redirect, url_for
import subprocess
import hmac
import hashlib

app = Flask(__name__)

# Midlertidige eksempeldata. Hent fra sencor
measurements = {
    "soil_moisture": 40,
    "temperature": 25,
    "humidity": 60,
    "nitrogen": 18,
    "phosphorus": 12,
    "potassium": 21,
}

settings = {
    "min_soil_moisture": 45,
    "max_temperature": 30,
    "min_humidity": 50,
    "auto_watering": True,
}

pump_active = False

history = [
    {"time": "10:00", "soil_moisture": 38, "temperature": 24, "humidity": 59},
    {"time": "10:15", "soil_moisture": 40, "temperature": 25, "humidity": 60},
    {"time": "10:30", "soil_moisture": 42, "temperature": 25, "humidity": 61},
    {"time": "10:45", "soil_moisture": 44, "temperature": 26, "humidity": 62},
]

events = [
    {"time": "10:00", "description": "Lav jordfugtighed registreret"},
    {"time": "10:10", "description": "Mulig mangel på fosfor fundet"},
    {"time": "10:20", "description": "Pumpen blev startet manuelt"},
]


def build_alerts():
    alerts = []

    if measurements["soil_moisture"] < settings["min_soil_moisture"]:
        alerts.append("Jordfugtigheden er under minimumsgrænsen.")

    if measurements["temperature"] > settings["max_temperature"]:
        alerts.append("Temperaturen er over den maksimale grænse.")

    if measurements["humidity"] < settings["min_humidity"]:
        alerts.append("Luftfugtigheden er under minimumsgrænsen.")

    if measurements["nitrogen"] < 15:
        alerts.append("Mulig mangel på kvælstof.")

    if measurements["phosphorus"] < 15:
        alerts.append("Mulig mangel på fosfor.")

    if measurements["potassium"] < 15:
        alerts.append("Mulig mangel på kalium.")

    return alerts


def build_nutrient_advice():
    advice = []

    if measurements["nitrogen"] < 15:
        advice.append("Planten mangler muligvis kvælstof.")
    if measurements["phosphorus"] < 15:
        advice.append("Planten mangler muligvis fosfor.")
    if measurements["potassium"] < 15:
        advice.append("Planten mangler muligvis kalium.")

    if not advice:
        advice.append("Næringsniveauerne ser normale ud.")

    return advice


def system_status(alerts):
    return "Advarsel" if alerts else "Normal"


@app.route("/")
def home():
    alerts = build_alerts()
    nutrient_advice = build_nutrient_advice()

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


@app.route("/history")
def history_page():
    return render_template("history.html", history=history, events=events)


@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    global settings

    if request.method == "POST":
        settings["min_soil_moisture"] = float(request.form.get("min_soil_moisture", 45))
        settings["max_temperature"] = float(request.form.get("max_temperature", 30))
        settings["min_humidity"] = float(request.form.get("min_humidity", 50))
        settings["auto_watering"] = request.form.get("auto_watering") == "on"

        events.insert(0, {"time": "Nu", "description": "Indstillinger blev opdateret"})
        return redirect(url_for("settings_page"))

    return render_template("settings.html", settings=settings)


@app.route("/water", methods=["POST"])
def water():
    global pump_active

    action = request.form.get("action")

    if action == "start":
        pump_active = True
        events.insert(0, {"time": "Nu", "description": "Pumpen blev startet manuelt"})
    elif action == "stop":
        pump_active = False
        events.insert(0, {"time": "Nu", "description": "Pumpen blev stoppet manuelt"})
    elif action == "toggle_auto":
        settings["auto_watering"] = not settings["auto_watering"]
        status = "til" if settings["auto_watering"] else "fra"
        events.insert(0, {"time": "Nu", "description": f"Auto-vanding blev slået {status}"})

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)

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

if __name__ == "__main__":
    app.run(debug=True)
