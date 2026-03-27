# Waveshare 3.6inch e-Paper E — Raspberry Pi

## Matériel
- Écran : Waveshare 3.6" e-Paper couleur (modèle E), 400×600 px
- Interface : SPI via GPIOs
- 6 couleurs : BLACK, WHITE, RED, BLUE, GREEN, YELLOW

## Structure
```
python/
├── examples/          ← nos scripts (lancer depuis ici)
├── lib/waveshare_epd/
│   ├── epd3in6e.py    ← driver principal (API publique ci-dessous)
│   └── epdconfig.py   ← couche bas niveau SPI/GPIO
├── pic/               ← images BMP de test + Font.ttc
└── setup.py
```

## Lancer un script
```bash
cd examples
python3 mon_script.py
```

## API du driver (epd3in6e.EPD)

```python
from waveshare_epd import epd3in6e

epd = epd3in6e.EPD()
epd.init()          # obligatoire avant tout affichage
epd.Clear()         # efface en blanc (lent ~15s)
epd.display(epd.getbuffer(image))  # affiche un PIL Image RGB 400×600
epd.sleep()         # mise en veille profonde (toujours finir par ça)
```

## Couleurs disponibles (valeurs BGR hex)
```python
epd.BLACK   = 0x000000
epd.WHITE   = 0xffffff
epd.YELLOW  = 0x00ffff
epd.RED     = 0x0000ff
epd.BLUE    = 0xff0000
epd.GREEN   = 0x00ff00
```

## Boilerplate type pour un exemple
```python
#!/usr/bin/python3
import sys, os
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir): sys.path.append(libdir)

import logging
from waveshare_epd import epd3in6e
from PIL import Image, ImageDraw, ImageFont
import time

logging.basicConfig(level=logging.DEBUG)

try:
    epd = epd3in6e.EPD()
    epd.init()
    epd.Clear()

    font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    img = Image.new('RGB', (epd.width, epd.height), epd.WHITE)
    draw = ImageDraw.Draw(img)

    # --- dessin ici ---

    epd.display(epd.getbuffer(img))
    time.sleep(3)

except KeyboardInterrupt:
    epd3in6e.epdconfig.module_exit(cleanup=True)
    exit()
finally:
    epd.sleep()
```

## Contraintes importantes
- `getbuffer()` fait une quantisation vers la palette 6 couleurs (avec dithering auto)
- L'image doit être en mode RGB, taille 400×600 (ou 600×400, auto-rotaté)
- `Clear()` et `display()` sont **lents** (~15-20s) : c'est normal, physique de l'encre
- Toujours appeler `epd.sleep()` en fin de script pour protéger l'écran
- Exécuter en `sudo` si erreur de permission GPIO/SPI

## Scripts existants
- `examples/hello_world.py` — Hello World avec démo couleurs
- `examples/photo.py` — Affiche une photo depuis URL ou fichier local (resize + dithering auto)
- `examples/clean.py` — Nettoyage / mise à blanc de l'écran
- `scripts/ai_image.py` — Générateur d'images IA, modes terminal et MQTT

## ai_image.py — providers IA

```bash
# Pollinations.ai (défaut, gratuit, sans token, modèle FLUX)
sudo -E /home/pi/.local/bin/uv run scripts/ai_image.py

# HuggingFace (token HF_TOKEN requis dans .env)
sudo -E /home/pi/.local/bin/uv run scripts/ai_image.py --provider huggingface

# Mode MQTT (service)
sudo -E /home/pi/.local/bin/uv run scripts/ai_image.py --mqtt
```

Provider par défaut : `pollinations`. Le quota gratuit HuggingFace (~1000 req/mois) est limité.

## Logs du service systemd

```bash
sudo journalctl -u epaper-ai.service -f        # temps réel
sudo journalctl -u epaper-ai.service -n 50     # 50 dernières lignes
```

## Test en mode dev

```bash
sudo systemctl stop epaper-ai.service
set -a && source .env && set +a
sudo -E /home/pi/.local/bin/uv run scripts/ai_image.py
```

## Contexte projet
- Usage pédagogique : labo de SI (Sciences de l'Ingénieur) avec des élèves
- Raspberry Pi 4, Debian Trixie (13) Lite sans X
- Réseau géré par NetworkManager (`nmcli`), pas wpa_supplicant directement

## Idées de projets pédagogiques
- Cadre photo connecté (cron + API Unsplash/Pexels)
- Compteur CO2 (capteur SCD41 + jauge colorée 6 couleurs)
- Dashboard de salle (emploi du temps, prochaine sonnerie)
- Afficheur de cantine (scraping menu)
- Station météo (capteur DHT22/BME280 + courbes)
- Panneau MQTT (chaque groupe publie du contenu)
- Générateur d'images IA (HuggingFace → dithering → affichage)
