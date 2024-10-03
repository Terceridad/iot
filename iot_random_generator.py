# pip install paho-mqtt

import paho.mqtt.client as mqtt
import random
import time
import json


MQTT_BROKER = "mqtt.eclipseprojects.io"
MQTT_PORT = 1883
MQTT_TOPIC = "pulsus/{0}/{1}/metrics"

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)


devices = {"b8f749f0-f491-402e-93f4-b629f001ce08": ["e39ef765-ebe0-4d14-9f58-fe2869960b5b",
                                                        "3ec8c5d6-9a39-48d5-84e6-9be1a6e56c05"],
               "cc7d36d6-4069-45b1-bcb6-ebdc76951b55": ["960731a7-ce08-474f-ac0b-73453f3eb99e",
                                                        "23a1cc56-c4ae-40e9-9c5d-7690c25e35cb"],
               "9f805bc1-24df-4f00-93cc-7fefc7c79ef1": ["d6f7a64f-9296-4dfc-b582-3d99e9b692c3",
                                                        "6b1818ce-48bf-47f0-a6e1-00ba694376ed"],
               "baf44b92-b52b-4f30-8f09-453b89fa5838": ["9d173a91-9eb0-4fd5-bd2c-f5ae1ad7f780"]
               }

def generate_health_metrics():
    if 1:
        return "0002AAEE01000000E2000000000031710101050064210001"
    else:
        return {
            "heart_rate": random.randint(60, 100),
            "blood_oxygen": round(random.uniform(95, 100), 1),
            "blood_pressure": {
                "systolic": random.randint(90, 140),
                "diastolic": random.randint(60, 90)
            },
            "blood_glucose": round(random.uniform(70, 140), 1),
            "sleep_hours": round(random.uniform(5, 9), 1),
            "mood": random.choice(["Happy", "Neutral", "Sad", "Excited", "Tired"])
        }

def publish_health_metrics():
    while True:
        gateway_id = random.choice(list(devices.keys()))
        device_id = random.choice(devices[gateway_id])
        topic = MQTT_TOPIC.format(gateway_id, device_id)

        metrics = generate_health_metrics()
        payload = json.dumps(metrics)
        client.publish(topic, payload)
        print(f"Topic: {topic}")