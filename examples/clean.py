#!/usr/bin/python3
"""Nettoyage et mise à blanc de l'écran e-Paper 3.6" (E)."""
import sys, os

libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd3in6e

logging.basicConfig(level=logging.DEBUG)

try:
    epd = epd3in6e.EPD()
    epd.init()
    epd.Clear()
    print("Écran nettoyé — prêt pour le rangement.")
except KeyboardInterrupt:
    epd3in6e.epdconfig.module_exit(cleanup=True)
    exit()
finally:
    epd.sleep()
