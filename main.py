from flask import Flask, request, abort
import subprocess
import hmac
import hashlib

app = Flask(__name__)

WEBHOOK_SECRET = "Shekib"
REPO_PATH = "/home/Ramsen0004/Eksamensprojekt-informatik"
WSGI_PATH = "/var/www/Ramsen0004_pythonanywhere_com_wsgi.py"

@app.route("/")
def home():
    return "Hej forsiden virker!"

@app.route("/update_server", methods=["GET", "POST"])
def update_server():
    return "Hej webhook virker!", 200

if __name__ == "__main__":
    app.run(debug=True)