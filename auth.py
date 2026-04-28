import requests

API_KEY = "AIzaSyDJu_tSpnCBjm3axi4RqoXtnXvpsul1yzE"

def login_user(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    response = requests.post(url, json={
        "email": email,
        "password": password,
        "returnSecureToken": True
    })
    return response.json()