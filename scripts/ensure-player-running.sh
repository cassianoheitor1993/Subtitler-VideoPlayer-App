#!/usr/bin/env bash
# Ensure SubtitlePlayer desktop app is running locally.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$ROOT_DIR/venv/bin/python"
ENTRY_PATH="$ROOT_DIR/main.py"
LOG_PATH="$ROOT_DIR/temp/headless.log"

get_alive_main_pids() {
  local pid
  for pid in $(pgrep -f 'SubtitlePlayer/main.py' || true); do
    if ps -p "$pid" > /dev/null 2>&1; then
      echo "$pid"
    fi
  done
}

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python virtualenv not found at $PYTHON_BIN" >&2
  exit 1
fi

legacy_pids="$(pgrep -f 'SubtitlePlayer/temp/start_cast.py' || true)"
if [[ -n "$legacy_pids" ]]; then
  echo "Stopping legacy start_cast.py process(es): $legacy_pids"
  pkill -f 'SubtitlePlayer/temp/start_cast.py' || true
fi

running_pids="$(get_alive_main_pids)"
if [[ -n "$running_pids" ]]; then
  running_pids="$(echo "$running_pids" | tr '\n' ' ')"
  echo "SubtitlePlayer already running with PID(s): $running_pids"
  exit 0
fi

echo "Launching SubtitlePlayer headlessly..."
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"
SUBTITLEPLAYER_DISABLE_SAMPLE_AUTOPLAY="${SUBTITLEPLAYER_DISABLE_SAMPLE_AUTOPLAY:-1}" \
  nohup "$PYTHON_BIN" "$ENTRY_PATH" \
    > "$LOG_PATH" 2>&1 &

sleep 2

running_pids="$(get_alive_main_pids)"
if [[ -z "$running_pids" ]]; then
  echo "Failed to launch SubtitlePlayer. Check $LOG_PATH for details." >&2
  exit 1
fi

running_pids="$(echo "$running_pids" | tr '\n' ' ')"
echo "SubtitlePlayer now running with PID(s): $running_pids"