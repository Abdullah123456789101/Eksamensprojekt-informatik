from flask import Flask, request, abort
import subprocess
import hmac
import hashlib

app = Flask(__name__)

WEBHOOK_SECRET = "Shekib"
REPO_PATH = "/home/Ramsen0004/Eksamensprojekt-informatik"
WSGI_PATH = "/var/www/Ramsen0004_pythonanywhere_com_wsgi.py"

@app.route("/update_server", methods=["POST"])
def update_server():
    print("Webhook called!")

    signature = request.headers.get("X-Hub-Signature-256")
    print("Signature:", signature)

    if not signature:
        return "No signature received", 403

    try:
        sha_name, signature = signature.split("=", 1)
    except ValueError:
        return "Bad signature format", 403

    print("SHA name:", sha_name)

    if sha_name != "sha256":
        return "Wrong hash type", 403

    mac = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        msg=request.data,
        digestmod=hashlib.sha256
    )

    calculated = mac.hexdigest()
    print("Calculated:", calculated)
    print("GitHub:", signature)

    if not hmac.compare_digest(calculated, signature):
        return f"Signature mismatch\nCalc: {calculated}\nGitHub: {signature}", 403

    event = request.headers.get("X-GitHub-Event", "")
    print("Event:", event)

    if event != "push":
        return "Ignoring non-push event", 200

    print("Pulling repo...")

    try:
        subprocess.check_call(["git", "-C", REPO_PATH, "pull"])
        subprocess.check_call(["touch", WSGI_PATH])
    except Exception as e:
        return f"Error during deploy: {e}", 500

    return "Updated successfully 🚀", 200