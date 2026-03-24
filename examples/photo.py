#!/usr/bin/python3
"""Affiche une photo sur l'écran e-Paper 3.6" (E) avec dithering auto."""
import sys, os

libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
import io
import urllib.request
from waveshare_epd import epd3in6e
from PIL import Image

logging.basicConfig(level=logging.DEBUG)

def get_image():
    """Récupère l'image depuis un fichier local ou une URL."""
    if len(sys.argv) >= 2:
        source = sys.argv[1].strip('"').strip("'")
    else:
        source = input("URL ou chemin vers une image (ex: https://picsum.photos/400/600): ").strip().strip('"').strip("'")

    if source.startswith(('http://', 'https://')):
        print(f"Téléchargement de {source}...")
        req = urllib.request.Request(source, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
        return Image.open(io.BytesIO(data)).convert('RGB')
    else:
        if not os.path.exists(source):
            print(f"Fichier introuvable: {source}")
            sys.exit(1)
        return Image.open(source).convert('RGB')

epd = None

try:
    img = get_image()
    print(f"Image originale: {img.size[0]}x{img.size[1]}")

    epd = epd3in6e.EPD()
    epd.init()

    # Redimensionner pour remplir l'écran en gardant le ratio
    target_w, target_h = epd.width, epd.height  # 400x600
    ratio = max(target_w / img.size[0], target_h / img.size[1])
    new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
    img = img.resize(new_size, Image.LANCZOS)

    # Crop centré
    left = (img.size[0] - target_w) // 2
    top = (img.size[1] - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    print(f"Redimensionné et croppé: {img.size[0]}x{img.size[1]}")

    # Affichage (getbuffer fait le dithering 6 couleurs)
    print("Envoi vers l'écran (~15s)...")
    epd.display(epd.getbuffer(img))
    print("Done!")

except KeyboardInterrupt:
    epd3in6e.epdconfig.module_exit(cleanup=True)
    exit()
finally:
    if epd:
        epd.sleep()
