#!/usr/bin/python3
"""Génère une image IA depuis un prompt et l'affiche sur l'écran e-Paper 3.6"."""
import sys, os

libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from huggingface_hub import InferenceClient
from waveshare_epd import epd3in6e
from PIL import Image

logging.basicConfig(level=logging.DEBUG)

epd = None

try:
    prompt = input("Décris l'image à générer : ").strip()
    if not prompt:
        print("Prompt vide, abandon.")
        sys.exit(1)

    print(f"Génération en cours pour : « {prompt} »...")
    client = InferenceClient()
    img = client.text_to_image(
        prompt,
        model="stabilityai/stable-diffusion-xl-base-1.0",
    )
    print(f"Image générée : {img.size[0]}x{img.size[1]}")

    # Resize + crop centré vers 400x600 (même logique que photo.py)
    epd = epd3in6e.EPD()
    target_w, target_h = epd.width, epd.height  # 400x600

    img = img.convert('RGB')
    ratio = max(target_w / img.size[0], target_h / img.size[1])
    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
    img = img.resize(new_size, Image.LANCZOS)

    left = (img.size[0] - target_w) // 2
    top = (img.size[1] - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    print(f"Redimensionné : {img.size[0]}x{img.size[1]}")

    # Affichage sur l'écran
    epd.init()
    print("Envoi vers l'écran (~15s)...")
    epd.display(epd.getbuffer(img))
    print("Done !")

except KeyboardInterrupt:
    epd3in6e.epdconfig.module_exit(cleanup=True)
    exit()
finally:
    if epd:
        epd.sleep()
