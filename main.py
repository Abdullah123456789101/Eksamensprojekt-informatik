from flask import Flask, request
import subprocess
import hmac
import hashlib

app = Flask(__name__)

WEBHOOK_SECRET = "Shekib"
REPO_PATH = "/home/Ramsen0004/Eksamensprojekt-informatik"
WSGI_PATH = "/var/www/Ramsen0004_pythonanywhere_com_wsgi.py"

@app.route("/")
def home():
    return "HUFHIEHF"

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