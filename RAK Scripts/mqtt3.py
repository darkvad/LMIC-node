#!/usr/bin/env python3
import json
import time
import paho.mqtt.client as mqtt
import base64

# ---------------- CONFIGURATION ----------------
BROKER = "localhost"
PORT = 1883

# ID de ton application ChirpStack (visible dans l'interface web)
APP_ID = "Sirenes_declencheur"

# Device EUI du capteur declencheur
TRIGGER_DEVICE = "24a16057cd50fefd"

# Liste des devices cibles a contacter
TARGET_DEVICES = [
    "00137a1000046f76",
    "1122334455667788"
]

# Contenu du message LoRa a envoyer (en Base64)
DOWNLINK_PAYLOAD = "kGkEAQAKAAAAAAA=" # "kGkBAQAFAAAAAAA=" sirene urgence  #"kGkEAQAKAAAAAAA=" sirene coupee # equivaut a 90690401000A0000000000

# ------------------------------------------------


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[OK] Connecta au broker MQTT local.")
        topic = f"application/+/device/+/rx"
        client.subscribe(topic)
        print(f"[MQTT] Abonne a {topic}")
    else:
        print(f"[ERREUR] Connexion MQTT echouee avec code {rc}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print("[ERREUR] Message JSON invalide.")
        return

    dev_eui = payload.get("devEUI")
    obj = payload.get("data", {})

    decoded_bytes = base64.b64decode(obj)
    decoded_hex = decoded_bytes.hex()
    print(f"\n.... Uplink recu de {dev_eui}: {obj} - {decoded_hex}")

    # --- Condition de declenchement ---
    #if dev_eui == TRIGGER_DEVICE and obj.get("trigger") == 1:
    if dev_eui == TRIGGER_DEVICE and decoded_bytes[1] == 0x00 and decoded_bytes[2] == 0x01:
        DOWNLINK_PAYLOAD = "kGkEAQAaAAAAAAA=" # demarrer alerte sirene coupee # equivaut a 90690401001A0000000000 26 sec# "kGkEAQA8AAAAAAA=" sirene coupee 60s
    if dev_eui == TRIGGER_DEVICE and decoded_bytes[1] == 0x01 and decoded_bytes[2] == 0x01:
        DOWNLINK_PAYLOAD = "kGkBAQAFAAAAAAA=" # demarrer alerte avec sirene #  "kGkBAQAFAAAAAAA=" sirene urgence 5s # "kGkBAQA8AAAAAAA=" Sirene urgence 60s
    if dev_eui == TRIGGER_DEVICE and decoded_bytes[2] == 0x00:
        DOWNLINK_PAYLOAD = "kGkEAAAAAAAAAAA=" # Arreter alerte # equivaut a 9069040000000000000000
    #if dev_eui == TRIGGER_DEVICE:
    if dev_eui == TRIGGER_DEVICE and (decoded_bytes[2] == 0x00 or decoded_bytes[2] == 0x01):
        print(f"......  Declenchement : envoi d'un downlink aux devices cibles...")

        for target in TARGET_DEVICES:
            downlink = {
                "confirmed": False,
                "fPort": 7,
                "data": DOWNLINK_PAYLOAD
            }

            topic_down = f"application/{APP_ID}/device/{target}/tx"
            client.publish(topic_down, json.dumps(downlink))
            print(f"   ... Downlink envoye a {target} sur {topic_down}")

        print("...  Envois termines.\n")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("[INFO] Connexion au broker MQTT local...")
client.connect(BROKER, PORT, 60)
client.loop_forever()
