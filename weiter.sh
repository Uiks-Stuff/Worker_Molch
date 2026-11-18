#!/usr/bin/env bash
# Startet Claude Code immer wieder mit /weiter, bis der Plan erledigt ist.
# Stoppen: Datei STOP im Projektordner anlegen (geht auch über die Samba-Freigabe) oder Strg+C.
cd "$(dirname "$0")" || exit 1
LOG=".claude/weiter.log"

log() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; }

while true; do
  if [ -f STOP ]; then log "STOP-Datei gefunden – beende."; rm -f STOP; break; fi
  if [ ! -f docs/PLAN.md ]; then log "Kein docs/PLAN.md – zuerst interaktiv /plan ausführen."; break; fi
  if grep -q '^STATUS: WARTE_AUF_FEEDBACK' docs/PROGRESS.md 2>/dev/null; then
    log "Wartet auf dein Feedback (docs/TESTS_FUER_DICH.md) – beende."; break
  fi
  if grep -q '^STATUS: FERTIG' docs/PROGRESS.md 2>/dev/null || ! grep -q -- '- \[ \]' docs/PLAN.md; then
    log "Alle Aufgaben erledigt – beende."; break
  fi

  log "Starte Durchlauf"
  claude -p "/weiter" --model sonnet --permission-mode acceptEdits >> "$LOG" 2>&1
  rc=$?

  if [ $rc -ne 0 ]; then
    log "Claude beendet mit Code $rc (vermutlich Nutzungslimit) – neuer Versuch in 30 Minuten."
    sleep 1800
  else
    sleep 60
  fi
done
