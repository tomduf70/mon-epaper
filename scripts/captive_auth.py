#!/usr/bin/python3
"""Authentification automatique au portail captif FortiGate."""
import sys, os, re
import urllib.request
import urllib.parse
import ssl

# Credentials depuis l'environnement ou .env
CAPTIVE_USERNAME = os.environ.get("CAPTIVE_USERNAME", "")
CAPTIVE_PASSWORD = os.environ.get("CAPTIVE_PASSWORD", "")

# Désactive la vérification SSL (certificat auto-signé du portail)
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE


def check_internet():
    """Vérifie si on a déjà accès à internet."""
    try:
        req = urllib.request.Request("http://detectportal.firefox.com/success.txt")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200 and "success" in resp.read().decode()
    except Exception:
        return False


def get_portal_url():
    """Détecte l'URL du portail captif via une requête HTTP."""
    try:
        req = urllib.request.Request("http://example.com")
        with urllib.request.urlopen(req, timeout=5) as resp:
            page = resp.read().decode()
        match = re.search(r'https://[^"<\s]+', page)
        return match.group(0) if match else None
    except Exception:
        return None


def get_magic_token(portal_url):
    """Récupère le magic token depuis la page du portail."""
    try:
        req = urllib.request.Request(portal_url)
        with urllib.request.urlopen(req, timeout=5, context=ssl_ctx) as resp:
            page = resp.read().decode()
        match = re.search(r'name="magic" value="([^"]+)"', page)
        return match.group(1) if match else None
    except Exception:
        return None


def authenticate(portal_url, magic):
    """Envoie les credentials au portail."""
    data = urllib.parse.urlencode({
        "4Tredir": "http://example.com/",
        "magic": magic,
        "username": CAPTIVE_USERNAME,
        "password": CAPTIVE_PASSWORD,
    }).encode()
    req = urllib.request.Request(portal_url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10, context=ssl_ctx) as resp:
            return resp.status == 200
    except Exception:
        return False


def main():
    if not CAPTIVE_USERNAME or not CAPTIVE_PASSWORD:
        print("CAPTIVE_USERNAME et CAPTIVE_PASSWORD requis dans .env")
        sys.exit(1)

    print("[1/4] Vérification de la connexion...")
    if check_internet():
        print("      Déjà connecté à internet.")
        return

    print("[2/4] Détection du portail captif...")
    portal_url = get_portal_url()
    if not portal_url:
        print("      Pas de portail détecté (réseau sans portail ?).")
        return
    print(f"      URL: {portal_url}")

    print("[3/4] Extraction du magic token...")
    magic = get_magic_token(portal_url)
    if not magic:
        print("      Erreur: impossible d'extraire le token.")
        sys.exit(1)
    print(f"      Magic: {magic}")

    print("[4/4] Authentification...")
    authenticate(portal_url, magic)

    if check_internet():
        print("      Authentification réussie !")
    else:
        print("      Échec de l'authentification.")
        sys.exit(1)


if __name__ == "__main__":
    main()
