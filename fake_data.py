import random

def generate_measurements():
    return {
        "soil_moisture": random.randint(20, 80),
        "temperature": random.randint(15, 30),
        "humidity": random.randint(30, 90),
        "nitrogen": random.randint(10, 30),
        "phosphorus": random.randint(5, 25),
        "potassium": random.randint(10, 30),
    }


def generate_event():
    events = [
        "Lav jordfugtighed registreret",
        "Temperaturen er høj",
        "Mulig mangel på kvælstof",
        "Mulig mangel på fosfor",
        "Mulig mangel på kalium",
    ]
    return random.choice(events)