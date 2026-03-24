#!/usr/bin/python3
import sys, os

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd3in6e
from PIL import Image, ImageDraw, ImageFont
import time

logging.basicConfig(level=logging.DEBUG)

try:
    epd = epd3in6e.EPD()
    epd.init()
    epd.Clear()

    # Création de l'image (400x600, fond blanc)
    img = Image.new('RGB', (epd.width, epd.height), epd.WHITE)
    draw = ImageDraw.Draw(img)

    # Polices
    font_big = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 48)
    font_small = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)

    # Titre centré en rouge
    draw.text((60, 200), "Hello World!", font=font_big, fill=epd.RED)

    # Sous-titre en bleu
    draw.text((80, 280), "e-Paper 3.6\" couleur", font=font_small, fill=epd.BLUE)

    # Petites démos de couleurs
    y = 350
    colors = [
        ("NOIR", epd.BLACK),
        ("ROUGE", epd.RED),
        ("BLEU", epd.BLUE),
        ("VERT", epd.GREEN),
        ("JAUNE", epd.YELLOW),
    ]
    for i, (name, color) in enumerate(colors):
        x = 40 + i * 70
        draw.rectangle([x, y, x + 50, y + 50], fill=color)
        draw.text((x + 5, y + 55), name, font=ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 12), fill=epd.BLACK)

    # Affichage
    epd.display(epd.getbuffer(img))
    time.sleep(3)

except KeyboardInterrupt:
    epd3in6e.epdconfig.module_exit(cleanup=True)
    exit()
finally:
    epd.sleep()
