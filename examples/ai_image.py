#!/usr/bin/python3
"""Génère une image IA depuis un prompt et l'affiche sur l'écran e-Paper 3.6"."""
import sys, os
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

    # Découpe le texte en lignes qui tiennent dans la largeur
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

    # On garde max 2 lignes
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
finally:
    epd.sleep()
    print("Écran en veille. À bientôt !")
