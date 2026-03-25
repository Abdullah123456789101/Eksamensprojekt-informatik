from flask import Flask, request, abort
import subprocess
import hmac
import hashlib

app = Flask(__name__)

WEBHOOK_SECRET = "skriv-en-lang-hemmelig-noegle-her"
REPO_PATH = "/home/Ramsen0004/Eksamensprojekt-informatik"
WSGI_PATH = "/var/www/Ramsen0004_pythonanywhere_com_wsgi.py"

@app.route("/update_server", methods=["POST"])
def update_server():
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        abort(403)

    sha_name, signature = signature.split("=", 1)
    if sha_name != "sha256":
        abort(403)

    mac = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        msg=request.data,
        digestmod=hashlib.sha256
    )

    if not hmac.compare_digest(mac.hexdigest(), signature):
        abort(403)

    event = request.headers.get("X-GitHub-Event", "")
    if event != "push":
        return "Ignoring non-push event", 200

    subprocess.check_call(["git", "-C", REPO_PATH, "pull"])
    subprocess.check_call(["touch", WSGI_PATH])

    return "Updated successfully", 200