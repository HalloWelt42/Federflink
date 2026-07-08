#!/usr/bin/env bash
#
# Federflink - Start- und Stop-Skript für Backend (FastAPI) und Frontend (Vite/Svelte).
#
# Verwendung:
#   ./start.sh start     Backend + Frontend starten (richtet beim ersten Mal alles ein)
#   ./start.sh stop      Backend + Frontend stoppen
#   ./start.sh restart   Backend + Frontend neu starten
#   ./start.sh status    Laufstatus anzeigen
#   ./start.sh logs      Logs live anzeigen (Strg+C zum Beenden)
#   ./start.sh setup     Abhängigkeiten (neu) installieren
#
set -euo pipefail

# ----------------------------------------------------------------------------
# Pfade und Konstanten
# ----------------------------------------------------------------------------
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUN_DIR="$ROOT_DIR/.run"
VENV_DIR="$BACKEND_DIR/.venv"

BACKEND_PID="$RUN_DIR/backend.pid"
FRONTEND_PID="$RUN_DIR/frontend.pid"
BACKEND_LOG="$RUN_DIR/backend.log"
FRONTEND_LOG="$RUN_DIR/frontend.log"
BACKEND_PORT_FILE="$RUN_DIR/backend.port"

# Wunsch-Port für das Backend (per ENV übersteuerbar). Ist er belegt, weicht
# das Skript auf den nächsten freien Port aus und reicht ihn an den Vite-Proxy
# weiter (frontend/vite.config.ts liest FEDERFLINK_API_PORT).
BACKEND_HOST="127.0.0.1"
PREFERRED_BACKEND_PORT="${FEDERFLINK_BACKEND_PORT:-8500}"
BACKEND_PORT="$PREFERRED_BACKEND_PORT"
FRONTEND_PORT="5195"

# ----------------------------------------------------------------------------
# Farbige Ausgabe (nur, wenn auf ein Terminal geschrieben wird)
# ----------------------------------------------------------------------------
if [ -t 1 ]; then
  C_RESET="\033[0m"; C_BOLD="\033[1m"
  C_GREEN="\033[32m"; C_YELLOW="\033[33m"; C_RED="\033[31m"; C_BLUE="\033[34m"
else
  C_RESET=""; C_BOLD=""; C_GREEN=""; C_YELLOW=""; C_RED=""; C_BLUE=""
fi

info() { printf '%b[i]%b %s\n'  "$C_BLUE"   "$C_RESET" "$*"; }
ok()   { printf '%b[ok]%b %s\n' "$C_GREEN"  "$C_RESET" "$*"; }
warn() { printf '%b[!]%b %s\n'  "$C_YELLOW" "$C_RESET" "$*" >&2; }
err()  { printf '%b[x]%b %s\n'  "$C_RED"    "$C_RESET" "$*" >&2; }
die()  { err "$*"; exit 1; }

# ----------------------------------------------------------------------------
# Hilfsfunktionen
# ----------------------------------------------------------------------------
detect_python() {
  local candidate
  for candidate in python3.13 python3.12 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 \
       && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 12) else 1)' >/dev/null 2>&1; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

read_pid() {
  local f="$1" pid
  [ -f "$f" ] || return 1
  pid="$(cat "$f" 2>/dev/null || true)"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 1
  printf '%s' "$pid"
}

pid_alive() { kill -0 "$1" 2>/dev/null; }

service_running() {
  local pid
  pid="$(read_pid "$1")" || return 1
  pid_alive "$pid" || return 1
  printf '%s' "$pid"
}

port_pids() { lsof -ti "tcp:$1" 2>/dev/null || true; }

kill_tree() {
  local pid="$1" sig="${2:-TERM}" child
  for child in $(pgrep -P "$pid" 2>/dev/null || true); do
    kill_tree "$child" "$sig"
  done
  kill "-$sig" "$pid" 2>/dev/null || true
}

find_free_port() {
  local port="$1" max=$(( $1 + 50 ))
  while [ "$port" -le "$max" ]; do
    [ -z "$(port_pids "$port")" ] && { printf '%s' "$port"; return 0; }
    port=$(( port + 1 ))
  done
  return 1
}

load_backend_port() {
  if [ -f "$BACKEND_PORT_FILE" ]; then
    BACKEND_PORT="$(cat "$BACKEND_PORT_FILE" 2>/dev/null || true)"
  fi
  [[ "${BACKEND_PORT:-}" =~ ^[0-9]+$ ]] || BACKEND_PORT="$PREFERRED_BACKEND_PORT"
}

# ----------------------------------------------------------------------------
# Abhängigkeiten einrichten (idempotent)
# ----------------------------------------------------------------------------
ensure_backend_deps() {
  local marker="$VENV_DIR/.deps-ok"
  [ -f "$marker" ] && return 0
  if [ ! -d "$VENV_DIR" ]; then
    local py
    py="$(detect_python)" || die "Kein Python >= 3.12 gefunden (wird für das Backend benötigt)."
    info "Lege Python-venv an ($("$py" --version 2>&1)) ..."
    "$py" -m venv "$VENV_DIR" || die "venv konnte nicht erstellt werden."
  fi
  info "Installiere Backend-Abhängigkeiten (einmalig, das kann etwas dauern) ..."
  "$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null 2>&1 || true
  "$VENV_DIR/bin/python" -m pip install -e "$BACKEND_DIR[dev]" \
    || die "pip install fehlgeschlagen (Ausgabe oben)."
  touch "$marker"
  ok "Backend-Abhängigkeiten installiert."
}

ensure_frontend_deps() {
  [ -d "$FRONTEND_DIR/node_modules/.bin" ] && return 0
  command -v npm >/dev/null 2>&1 || die "npm nicht gefunden (wird für das Frontend benötigt)."
  info "Installiere Frontend-Abhängigkeiten (einmalig, das kann etwas dauern) ..."
  ( cd "$FRONTEND_DIR" && npm install ) || die "npm install fehlgeschlagen."
  ok "Frontend-Abhängigkeiten installiert."
}

# ----------------------------------------------------------------------------
# Warten auf Bereitschaft
# ----------------------------------------------------------------------------
wait_backend_ready() {
  local i
  for (( i = 0; i < 60; i++ )); do
    service_running "$BACKEND_PID" >/dev/null || return 2
    if curl -fsS -o /dev/null "http://$BACKEND_HOST:$BACKEND_PORT/api/health" 2>/dev/null; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

wait_frontend_ready() {
  local i
  for (( i = 0; i < 120; i++ )); do
    service_running "$FRONTEND_PID" >/dev/null || return 2
    [ -n "$(port_pids "$FRONTEND_PORT")" ] && return 0
    sleep 0.5
  done
  return 1
}

# ----------------------------------------------------------------------------
# Starten
# ----------------------------------------------------------------------------
start_backend() {
  mkdir -p "$RUN_DIR"
  local pid
  if pid="$(service_running "$BACKEND_PID")"; then
    load_backend_port
    info "Backend läuft bereits (PID $pid, Port $BACKEND_PORT)."
    return 0
  fi
  if [ -n "$(port_pids "$PREFERRED_BACKEND_PORT")" ]; then
    BACKEND_PORT="$(find_free_port "$PREFERRED_BACKEND_PORT")" \
      || die "Kein freier Port ab $PREFERRED_BACKEND_PORT gefunden."
    warn "Port $PREFERRED_BACKEND_PORT ist belegt - Backend nutzt stattdessen Port $BACKEND_PORT."
  else
    BACKEND_PORT="$PREFERRED_BACKEND_PORT"
  fi
  echo "$BACKEND_PORT" >"$BACKEND_PORT_FILE"

  ensure_backend_deps
  [ -x "$VENV_DIR/bin/uvicorn" ] || die "uvicorn fehlt im venv. './start.sh setup' ausführen oder backend/.venv löschen."

  info "Starte Backend auf http://$BACKEND_HOST:$BACKEND_PORT ..."
  ( cd "$BACKEND_DIR" && exec nohup env FEDERFLINK_PORT="$BACKEND_PORT" "$VENV_DIR/bin/uvicorn" app.main:app \
      --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload \
  ) >"$BACKEND_LOG" 2>&1 &
  echo $! >"$BACKEND_PID"

  case "$(wait_backend_ready; echo $?)" in
    0) ok "Backend bereit (PID $(cat "$BACKEND_PID"))." ;;
    *)
      err "Backend nicht erreichbar. Letzte Log-Zeilen:"
      tail -n 25 "$BACKEND_LOG" 2>/dev/null || true
      stop_service "Backend" "$BACKEND_PID" "$BACKEND_PORT"
      die "Backend-Start fehlgeschlagen."
      ;;
  esac
}

start_frontend() {
  mkdir -p "$RUN_DIR"
  local pid
  if pid="$(service_running "$FRONTEND_PID")"; then
    info "Frontend läuft bereits (PID $pid)."
    return 0
  fi
  if [ -n "$(port_pids "$FRONTEND_PORT")" ]; then
    die "Port $FRONTEND_PORT ist bereits belegt. Erst './start.sh stop' oder den Port freigeben."
  fi
  ensure_frontend_deps
  [ -n "${BACKEND_PORT:-}" ] && [[ "$BACKEND_PORT" =~ ^[0-9]+$ ]] || load_backend_port

  info "Starte Frontend auf http://localhost:$FRONTEND_PORT ..."
  ( cd "$FRONTEND_DIR" && exec nohup env FEDERFLINK_API_PORT="$BACKEND_PORT" npm run dev ) >"$FRONTEND_LOG" 2>&1 &
  echo $! >"$FRONTEND_PID"

  case "$(wait_frontend_ready; echo $?)" in
    0) ok "Frontend bereit (PID $(cat "$FRONTEND_PID"))." ;;
    *)
      err "Frontend nicht erreichbar. Letzte Log-Zeilen:"
      tail -n 25 "$FRONTEND_LOG" 2>/dev/null || true
      stop_service "Frontend" "$FRONTEND_PID" "$FRONTEND_PORT"
      die "Frontend-Start fehlgeschlagen."
      ;;
  esac
}

# ----------------------------------------------------------------------------
# Stoppen
# ----------------------------------------------------------------------------
stop_service() {
  local name="$1" pidfile="$2" port="$3" stopped=0 pid i leftovers
  if pid="$(service_running "$pidfile")"; then
    info "Stoppe $name (PID $pid) ..."
    kill_tree "$pid" TERM
    for (( i = 0; i < 20; i++ )); do
      pid_alive "$pid" || break
      sleep 0.25
    done
    if pid_alive "$pid"; then
      warn "$name reagiert nicht, erzwinge Stop ..."
      kill_tree "$pid" KILL
    fi
    stopped=1
  fi
  rm -f "$pidfile"
  if [ -n "$port" ]; then
    leftovers="$(port_pids "$port")"
    if [ -n "$leftovers" ]; then
      info "Räume verbliebene Prozesse auf Port $port auf ..."
      # shellcheck disable=SC2086
      kill $leftovers 2>/dev/null || true
      sleep 0.5
      leftovers="$(port_pids "$port")"
      if [ -n "$leftovers" ]; then
        # shellcheck disable=SC2086
        kill -9 $leftovers 2>/dev/null || true
      fi
      stopped=1
    fi
  fi
  if [ "$stopped" -eq 1 ]; then
    ok "$name gestoppt."
  else
    info "$name lief nicht."
  fi
}

# ----------------------------------------------------------------------------
# Status
# ----------------------------------------------------------------------------
status_line() {
  local name="$1" pidfile="$2" port="$3" url="$4" pid
  if pid="$(service_running "$pidfile")"; then
    printf '  %b%-9s%b läuft      (PID %-6s) %s\n' "$C_GREEN" "$name" "$C_RESET" "$pid" "$url"
  elif [ -n "$port" ] && [ -n "$(port_pids "$port")" ]; then
    printf '  %b%-9s%b Port %s belegt (ohne PID-Datei)\n' "$C_YELLOW" "$name" "$C_RESET" "$port"
  else
    printf '  %b%-9s%b gestoppt\n' "$C_RED" "$name" "$C_RESET"
  fi
}

# ----------------------------------------------------------------------------
# Kommandos
# ----------------------------------------------------------------------------
cmd_start() {
  mkdir -p "$RUN_DIR"
  start_backend
  start_frontend
  echo
  ok "Federflink läuft."
  printf '  Frontend:  %bhttp://localhost:%s%b\n' "$C_BOLD" "$FRONTEND_PORT" "$C_RESET"
  printf '  Backend:   http://%s:%s   (API-Doku über den Proxy: http://localhost:%s/docs)\n' "$BACKEND_HOST" "$BACKEND_PORT" "$FRONTEND_PORT"
  printf '  Logs:      .run/backend.log  .run/frontend.log\n'
  printf '  Stoppen:   ./start.sh stop\n'
}

cmd_stop() {
  local bport=""
  if [ -f "$BACKEND_PORT_FILE" ]; then
    bport="$(cat "$BACKEND_PORT_FILE" 2>/dev/null || true)"
    [[ "$bport" =~ ^[0-9]+$ ]] || bport=""
  fi
  stop_service "Frontend" "$FRONTEND_PID" "$FRONTEND_PORT"
  stop_service "Backend"  "$BACKEND_PID"  "$bport"
  rm -f "$BACKEND_PORT_FILE"
  ok "Federflink gestoppt."
}

cmd_restart() {
  cmd_stop
  echo
  cmd_start
}

cmd_status() {
  printf '%bFederflink-Status%b\n' "$C_BOLD" "$C_RESET"
  local bport=""
  if [ -f "$BACKEND_PORT_FILE" ]; then
    bport="$(cat "$BACKEND_PORT_FILE" 2>/dev/null || true)"
    [[ "$bport" =~ ^[0-9]+$ ]] || bport=""
  fi
  status_line "Backend"  "$BACKEND_PID"  "$bport"  "http://$BACKEND_HOST:${bport:-$PREFERRED_BACKEND_PORT}"
  status_line "Frontend" "$FRONTEND_PID" "$FRONTEND_PORT" "http://localhost:$FRONTEND_PORT"
}

cmd_logs() {
  local files=()
  [ -f "$BACKEND_LOG" ]  && files+=("$BACKEND_LOG")
  [ -f "$FRONTEND_LOG" ] && files+=("$FRONTEND_LOG")
  [ "${#files[@]}" -eq 0 ] && { info "Noch keine Logs vorhanden."; return 0; }
  info "Folge Logs (Strg+C zum Beenden) ..."
  tail -n 20 -f "${files[@]}"
}

cmd_setup() {
  mkdir -p "$RUN_DIR"
  rm -f "$VENV_DIR/.deps-ok"
  ensure_backend_deps
  command -v npm >/dev/null 2>&1 || die "npm nicht gefunden."
  info "Aktualisiere Frontend-Abhängigkeiten ..."
  ( cd "$FRONTEND_DIR" && npm install ) || die "npm install fehlgeschlagen."
  ok "Setup abgeschlossen."
}

usage() {
  cat <<'EOF'
Federflink - Start/Stop

  ./start.sh           Diese Übersicht anzeigen
  ./start.sh start     Backend + Frontend starten
  ./start.sh stop      Backend + Frontend stoppen
  ./start.sh restart   Backend + Frontend neu starten
  ./start.sh status    Laufstatus anzeigen
  ./start.sh logs      Logs live anzeigen (Strg+C zum Beenden)
  ./start.sh setup     Abhängigkeiten (neu) installieren

Beim ersten Start werden venv und npm-Pakete automatisch eingerichtet.
Frontend: http://localhost:5195    Backend: 127.0.0.1:8500 (oder nächster freier Port)
EOF
}

# ----------------------------------------------------------------------------
# Einstiegspunkt
# ----------------------------------------------------------------------------
case "${1:-}" in
  start)         cmd_start ;;
  stop)          cmd_stop ;;
  restart)       cmd_restart ;;
  status)        cmd_status ;;
  logs)          cmd_logs ;;
  setup)         cmd_setup ;;
  ""|-h|--help|help) usage ;;
  *) err "Unbekanntes Kommando: $1"; echo; usage; exit 1 ;;
esac
