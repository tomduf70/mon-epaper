# mon-epaper

Projets pédagogiques autour d'un écran **Waveshare 3.6" e-Paper (E)** 6 couleurs piloté par un **Raspberry Pi 4**.

## Matériel

- Raspberry Pi 4 — Debian Trixie Lite (sans X)
- Waveshare 3.6" e-Paper couleur (modèle E) — 400x600 px, SPI
- 6 couleurs : noir, blanc, rouge, bleu, vert, jaune

## Installation

```bash
# Prérequis système (une seule fois)
sudo apt install swig liblgpio-dev

# Cloner et installer les dépendances
git clone https://github.com/tomduf70/mon-epaper.git
cd mon-epaper
uv sync
```

## Configuration

Créer un fichier `.env` à la racine avec votre token HuggingFace :

```
HF_TOKEN=hf_votre_token_ici
```

Obtenir un token gratuit sur [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).

## Scripts

Tous les scripts se lancent depuis `examples/` :

```bash
cd examples
uv run <script>.py
```

| Script | Description |
|--------|-------------|
| `hello_world.py` | Hello World + démo des 6 couleurs |
| `photo.py` | Affiche une photo (URL ou fichier local) avec dithering auto |
| `clean.py` | Nettoyage / mise à blanc de l'écran |
| `ai_image.py` | Générateur d'images IA (HuggingFace SDXL) |

## Générateur d'images IA

Le script principal du projet. Génère une image à partir d'un prompt texte via l'API HuggingFace et l'affiche sur l'écran e-paper.

### Mode terminal

```bash
uv run ai_image.py
# → tape ton prompt, l'image apparaît sur l'écran
# → enchaîne les prompts, 'q' pour quitter
```

### Mode MQTT

```bash
uv run ai_image.py --mqtt
```

Écoute le broker MQTT `broker.mqttdashboard.com` sur les topics :

| Topic | Direction | Description |
|-------|-----------|-------------|
| `palissy/epaper/prompt` | entrant | Prompt texte à générer |
| `palissy/epaper/status` | sortant | Statut : `ready`, `generating`, `error` |
| `palissy/epaper/shutdown` | entrant | Éteint le Raspberry Pi |

### Chaîne complète (démo portes ouvertes)

```
Raccourci iOS (dictée vocale)
  → POST JSON {"prompt": "..."} vers Node-RED (Cloudflare)
    → MQTT broker public
      → Raspberry Pi
        → HuggingFace (génération SDXL)
          → écran e-paper
```

Le prompt est affiché en bas de l'image sur un bandeau noir (2 lignes max).
Les images sont sauvegardées dans `generated/` avec horodatage.

### Démarrage automatique (systemd)

```bash
sudo cp epaper-ai.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable epaper-ai
sudo systemctl start epaper-ai
```

## Exemples d'images générées

| | |
|---|---|
| ![astronaute](generated/20260325_185711.png) | ![chaton](generated/20260325_194513.png) |
| ![chaton 2](generated/20260325_201054.png) | ![plage](generated/20260325_201455.png) |

## Structure du projet

```
├── examples/
│   ├── ai_image.py        ← générateur IA (terminal + MQTT)
│   ├── hello_world.py     ← démo couleurs
│   ├── photo.py           ← affichage photo
│   └── clean.py           ← nettoyage écran
├── lib/waveshare_epd/
│   ├── epd3in6e.py        ← driver e-paper
│   └── epdconfig.py       ← couche SPI/GPIO
├── pic/                   ← polices + images de test
├── generated/             ← images IA générées
├── epaper-ai.service      ← service systemd
├── pyproject.toml         ← dépendances (uv)
└── .env                   ← token HuggingFace (non committé)
```

## Dépendances Python

Gérées par [uv](https://docs.astral.sh/uv/) :

- `huggingface-hub` — API Inference HuggingFace
- `pillow` — manipulation d'images
- `paho-mqtt` — client MQTT
- `spidev` / `gpiozero` / `rpi-lgpio` — interface matérielle

## Licence

Usage pédagogique — Lycée Palissy.
