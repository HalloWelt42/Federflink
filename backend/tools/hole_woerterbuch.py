#!/usr/bin/env python3
"""Lädt das deutsche Hunspell-Wörterbuch (für die Rechtschreibprüfung).

Die Dateien werden nach data/woerterbuecher/de_DE.aff und de_DE.dic gelegt.
Quelle: igerman98-basierte Wörterbücher (siehe LICENSE, Drittanbieter). Das
Wörterbuch wird bewusst nicht ins Repo eingecheckt, sondern bei Bedarf geladen.

Aufruf:
    python tools/hole_woerterbuch.py
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

# Projektwurzel/Datenverzeichnis unabhängig vom Arbeitsverzeichnis bestimmen.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import config  # noqa: E402

QUELLEN: dict[str, str] = {
    "de_DE.aff": "https://raw.githubusercontent.com/wooorm/dictionaries/main/dictionaries/de/index.aff",
    "de_DE.dic": "https://raw.githubusercontent.com/wooorm/dictionaries/main/dictionaries/de/index.dic",
    # Häufigkeitsliste für die Wortvervollständigung (Wort + Zähler je Zeile).
    "de_frequenz.txt": "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/de/de_50k.txt",
}


def hole(ziel_verzeichnis: Path) -> None:
    ziel_verzeichnis.mkdir(parents=True, exist_ok=True)
    for dateiname, url in QUELLEN.items():
        ziel = ziel_verzeichnis / dateiname
        print(f"Lade {dateiname} ...", flush=True)
        with urllib.request.urlopen(url, timeout=30) as antwort:  # noqa: S310 - feste, vertrauenswürdige URL
            daten = antwort.read()
        ziel.write_bytes(daten)
        print(f"  -> {ziel} ({len(daten)} Bytes)")
    print("Fertig. Deutsches Wörterbuch bereit.")


if __name__ == "__main__":
    hole(config.WOERTERBUCH_VERZEICHNIS)
