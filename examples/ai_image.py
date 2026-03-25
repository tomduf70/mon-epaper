#!/usr/bin/python3
"""Génère une image IA depuis un prompt et l'affiche sur l'écran e-Paper 3.6".

Deux modes :
  python3 ai_image.py          → mode terminal interactif
  python3 ai_image.py --mqtt   → écoute le topic MQTT epaper/prompt
"""
import sys, os, argparse
from datetime import datetime

libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
savedir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'generated')
os.makedirs(savedir, exist_ok=True)

import logging
from huggingface_hub import InferenceClient
from waveshare_epd import epd3in6e
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.DEBUG)

MQTT_BROKER = "nas-si-b01"
MQTT_PORT = 1883
MQTT_TOPIC = "epaper/prompt"
MQTT_TOPIC_STATUS = "epaper/status"

client = InferenceClient()
epd = epd3in6e.EPD()
font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 16)


def generate_and_display(prompt):
    """Génère une image, l'affiche sur l'écran et la sauvegarde."""
    print(f"Génération en cours pour : « {prompt} »...")
    img = client.text_to_image(
        prompt,
        model="stabilityai/stable-diffusion-xl-base-1.0",
    )
    print(f"Image générée : {img.size[0]}x{img.size[1]}")

    # Resize + crop centré vers 400x600
    target_w, target_h = epd.width, epd.height  # 400x600
    img = img.convert('RGB')
    ratio = max(target_w / img.size[0], target_h / img.size[1])
    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
    img = img.resize(new_size, Image.LANCZOS)

    left = (img.size[0] - target_w) // 2
    top = (img.size[1] - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    # Ajout du prompt en bas de l'image (2 lignes max)
    draw = ImageDraw.Draw(img)
    margin = 6
    max_width = target_w - 2 * margin

    words = prompt.split()
    lines = []
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip()
        if draw.textlength(test, font=font) <= max_width:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    lines = lines[:2]
    if len(lines) == 2 and draw.textlength(lines[1], font=font) > max_width:
        lines[1] = lines[1][:40] + "..."

    line_height = 20
    block_height = len(lines) * line_height + 2 * margin
    text_y = target_h - block_height
    draw.rectangle([0, text_y, target_w, target_h], fill=epd.BLACK)
    for i, line in enumerate(lines):
        draw.text((margin, text_y + margin + i * line_height), line, font=font, fill=epd.WHITE)

    # Sauvegarde
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(savedir, f"{timestamp}.png")
    img.save(filename)
    print(f"Image sauvegardée : {filename}")

    # Affichage sur l'écran
    epd.init()
    print("Envoi vers l'écran (~15s)...")
    epd.display(epd.getbuffer(img))
    print("Done !")


def run_terminal():
    """Mode terminal interactif."""
    try:
        while True:
            prompt = input("\nDécris l'image à générer (ou 'q' pour quitter) : ").strip()
            if not prompt:
                continue
            if prompt.lower() == 'q':
                break
            generate_and_display(prompt)
    except KeyboardInterrupt:
        print("\nInterruption.")


def run_mqtt():
    """Mode MQTT : écoute le topic et génère à chaque message."""
    import paho.mqtt.client as mqtt

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    def on_connect(client, userdata, flags, rc, properties):
        print(f"Connecté au broker MQTT {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        client.publish(MQTT_TOPIC_STATUS, "ready")
        print(f"En attente de prompts sur {MQTT_TOPIC}...")

    def on_message(client, userdata, msg):
        prompt = msg.payload.decode("utf-8").strip()
        if not prompt:
            return
        print(f"\n--- Nouveau prompt reçu via MQTT ---")
        client.publish(MQTT_TOPIC_STATUS, "generating")
        try:
            generate_and_display(prompt)
            client.publish(MQTT_TOPIC_STATUS, "ready")
        except Exception as e:
            print(f"Erreur : {e}")
            client.publish(MQTT_TOPIC_STATUS, f"error: {e}")

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("\nInterruption.")
        mqtt_client.publish(MQTT_TOPIC_STATUS, "offline")
        mqtt_client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Générateur d'images IA pour e-Paper")
    parser.add_argument("--mqtt", action="store_true", help="Mode MQTT (écoute epaper/prompt)")
    args = parser.parse_args()

    try:
        if args.mqtt:
            run_mqtt()
        else:
            run_terminal()
    finally:
        epd.sleep()
        print("Écran en veille. À bientôt !")
