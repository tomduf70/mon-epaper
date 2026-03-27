#!/usr/bin/python3
"""Génère une image IA depuis un prompt et l'affiche sur l'écran e-Paper 3.6".

Deux modes :
  python3 ai_image.py          → mode terminal interactif
  python3 ai_image.py --mqtt   → écoute le topic MQTT epaper/prompt

Providers disponibles :
  --provider pollinations  → Pollinations.ai (gratuit, sans token, défaut)
  --provider huggingface   → HuggingFace Inference API (token HF_TOKEN requis)
"""
import sys, os, argparse, io, random
from datetime import datetime
from urllib.parse import quote

libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
savedir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'generated')
os.makedirs(savedir, exist_ok=True)

import logging
import requests
from waveshare_epd import epd3in6e
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO)

MQTT_BROKER = "broker.mqttdashboard.com"
MQTT_PORT = 1883
MQTT_TOPIC = "palissy/epaper/prompt"
MQTT_TOPIC_STATUS = "palissy/epaper/status"
MQTT_TOPIC_SHUTDOWN = "palissy/epaper/shutdown"
MQTT_TOPIC_CLEAN = "palissy/epaper/clean"
MQTT_TOPIC_RANDOM = "palissy/epaper/random"

PROVIDER = "pollinations"  # valeur par défaut, remplacée par l'argument CLI

epd = epd3in6e.EPD()
font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 16)


def fetch_image_pollinations(prompt):
    """Génère une image via Pollinations.ai."""
    # gen.pollinations.ai est le nouvel endpoint (image.pollinations.ai redirige là mais
    # requests perd les headers Referer/Origin sur les redirects cross-domaine)
    url = f"https://gen.pollinations.ai/image/{quote(prompt)}"
    params = {"width": 1024, "height": 1024, "model": "flux", "nologo": "true"}
    token = os.environ.get("POLLINATIONS_TOKEN")
    if token:
        params["key"] = token
    headers = {
        "Referer": "https://pollinations.ai",
        "Origin": "https://pollinations.ai",
        "User-Agent": "Mozilla/5.0 (X11; Linux aarch64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    }
    print(f"Appel Pollinations.ai...")
    response = requests.get(url, params=params, headers=headers, timeout=120)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGB")


def fetch_image_huggingface(prompt):
    """Génère une image via HuggingFace Inference API (token requis)."""
    from huggingface_hub import InferenceClient
    hf_client = InferenceClient()
    print(f"Appel HuggingFace Inference API...")
    return hf_client.text_to_image(
        prompt,
        model="stabilityai/stable-diffusion-xl-base-1.0",
    )


def display_random():
    """Affiche une image aléatoire depuis le dossier generated/."""
    images = [f for f in os.listdir(savedir) if f.lower().endswith('.png')]
    if not images:
        print("Aucune image dans le dossier generated/.")
        return
    filename = random.choice(images)
    path = os.path.join(savedir, filename)
    print(f"Image aléatoire : {filename}")
    img = Image.open(path).convert("RGB")

    target_w, target_h = epd.width, epd.height
    ratio = max(target_w / img.size[0], target_h / img.size[1])
    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
    img = img.resize(new_size, Image.LANCZOS)
    left = (img.size[0] - target_w) // 2
    top = (img.size[1] - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    epd.init()
    print("Envoi vers l'écran (~15s)...")
    epd.display(epd.getbuffer(img))
    print("Done !")


def generate_and_display(prompt):
    """Génère une image, l'affiche sur l'écran et la sauvegarde."""
    print(f"Génération en cours pour : « {prompt} » (provider: {PROVIDER})...")
    if PROVIDER == "huggingface":
        img = fetch_image_huggingface(prompt)
    else:
        img = fetch_image_pollinations(prompt)
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
        print(f"Connecté au broker MQTT")
        client.subscribe(MQTT_TOPIC)
        client.subscribe(MQTT_TOPIC_SHUTDOWN)
        client.subscribe(MQTT_TOPIC_CLEAN)
        client.subscribe(MQTT_TOPIC_RANDOM)
        client.publish(MQTT_TOPIC_STATUS, "ready")
        print(f"En attente de prompts sur {MQTT_TOPIC}...")

    def on_message(client, userdata, msg):
        if msg.topic == MQTT_TOPIC_SHUTDOWN:
            print("\n--- Extinction demandée via MQTT ---")
            client.publish(MQTT_TOPIC_STATUS, "shutting down")
            client.disconnect()
            epd.sleep()
            os.system("sudo shutdown -h now")
            return

        if msg.topic == MQTT_TOPIC_RANDOM:
            print("\n--- Image aléatoire demandée via MQTT ---")
            client.publish(MQTT_TOPIC_STATUS, "displaying")
            try:
                display_random()
                client.publish(MQTT_TOPIC_STATUS, "ready")
            except Exception as e:
                print(f"Erreur : {e}")
                client.publish(MQTT_TOPIC_STATUS, f"error: {e}")
            return

        if msg.topic == MQTT_TOPIC_CLEAN:
            print("\n--- Nettoyage demandé via MQTT ---")
            client.publish(MQTT_TOPIC_STATUS, "cleaning")
            try:
                epd.init()
                epd.Clear()
                print("Écran nettoyé.")
                client.publish(MQTT_TOPIC_STATUS, "ready")
            except Exception as e:
                print(f"Erreur nettoyage : {e}")
                client.publish(MQTT_TOPIC_STATUS, f"error: {e}")
            return

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

    import signal

    def handle_exit(sig, frame):
        print("\nArrêt du script...")
        mqtt_client.publish(MQTT_TOPIC_STATUS, "offline")
        mqtt_client.disconnect()
        mqtt_client.loop_stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Générateur d'images IA pour e-Paper")
    parser.add_argument("--mqtt", action="store_true", help="Mode MQTT (écoute epaper/prompt)")
    parser.add_argument("--provider", choices=["pollinations", "huggingface"],
                        default="pollinations",
                        help="Provider IA : pollinations (défaut, gratuit) ou huggingface (token requis)")
    args = parser.parse_args()

    PROVIDER = args.provider

    try:
        if args.mqtt:
            run_mqtt()
        else:
            run_terminal()
    finally:
        epd.sleep()
        print("Écran en veille. À bientôt !")
