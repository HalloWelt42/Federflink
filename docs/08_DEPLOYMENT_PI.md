# Federflink - Betrieb auf dem Pi5

Federflink laeuft auf einem Raspberry Pi 5 (8-16 GB RAM) als zentraler Dienst im
Heimnetz. Backend und Frontend laufen bare, das Sprachmodell ueber Ollama.

## 1. Voraussetzungen

- Raspberry Pi OS (64-bit), Python >= 3.12, Node.js/npm, `git`.
- Genug RAM fuer ein kleines Modell (siehe [09_MODELLE.md](09_MODELLE.md)).

## 2. Sprachmodell (Ollama)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:1.5b-instruct        # Ergaenzung/Korrektur
ollama pull bge-m3                        # Embeddings (Umfeld-Kontext)
```

Ollama stellt eine OpenAI-kompatible API unter `http://localhost:11434` bereit.
In Federflink die LLM-URL entsprechend setzen (Umgebungsvariable oder Einstellungen):

```bash
export FEDERFLINK_LLM_URL="http://localhost:11434"
export FEDERFLINK_CHAT_MODELL="qwen2.5:1.5b-instruct"
export FEDERFLINK_EMBEDDING_MODELL="bge-m3"
```

Hunspell (spylls) braucht kein Java. LanguageTool ist optional (Java, ~1 GB) und
kann auf dem Pi abgeschaltet bleiben.

## 3. Federflink starten

```bash
git clone <repo> federflink && cd federflink
./backend/tools/hole_woerterbuch.py     # deutsches Woerterbuch + Frequenzliste laden
./start.sh start                        # Backend :8500, Frontend :5195
```

Datenbank und Woerterbuecher liegen unter `data/` auf dem lokalen Dateisystem
(ext4). Keine SQLite-Datei auf ein Netzlaufwerk oder einen exFAT-Datentraeger
legen (WAL-Journal kann dort korrumpieren).

## 4. Autostart (systemd)

`/etc/systemd/system/federflink.service`:

```ini
[Unit]
Description=Federflink
After=network-online.target ollama.service

[Service]
Type=forking
User=pi
WorkingDirectory=/home/pi/federflink
Environment=FEDERFLINK_LLM_URL=http://localhost:11434
Environment=FEDERFLINK_CHAT_MODELL=qwen2.5:1.5b-instruct
Environment=FEDERFLINK_EMBEDDING_MODELL=bge-m3
ExecStart=/home/pi/federflink/start.sh start
ExecStop=/home/pi/federflink/start.sh stop
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now federflink
```

## 5. Zugriff aus dem Netz

- Andere Geraete erreichen die Oberflaeche unter `http://<pi-ip>:5195`.
- Die Browser-Erweiterung: Server-URL auf `http://<pi-ip>:8500` setzen und in
  `extension/manifest.json` unter `host_permissions` `http://<pi-ip>:8500/*`
  ergaenzen, dann neu laden.
- Optional HTTPS ueber einen lokalen Reverse-Proxy (z. B. Caddy) fuer PWA-/
  Sicherheitskomfort.

## 6. Ressourcen

Ein 1.5B-Instruct-Modell (Q4) belegt ~1-1.5 GB RAM und liefert auf dem Pi5 kurze
Ergaenzungen in wenigen hundert Millisekunden. Rechtschreibung (Hunspell) und
Trie/N-Gramm laufen praktisch sofort und ohne Modell.
