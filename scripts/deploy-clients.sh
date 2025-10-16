#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"

ANDROID_SCRIPT="${SCRIPT_DIR}/build-android-client.sh"
VIDAA_SCRIPT="${SCRIPT_DIR}/package-vidaa-client.sh"

RUN_ANDROID=1
RUN_VIDAA=1
ANDROID_VARIANT="release"
VIDAA_CONFIG=""
VIDAA_OUTPUT="SubtitleCast"

show_help() {
  cat <<'EOF'
Usage: deploy-clients.sh [options]

Builds the Android CastPlayer APK and packages the VIDAA SubtitleCast app.

Options:
  --android-only           Only build the Android APK
  --vidaa-only             Only package the VIDAA app
  --android-variant VAR    Build variant for Android (release|debug)
  --vidaa-config FILE      Override config.json for VIDAA packaging
  --vidaa-output NAME      Output base name for VIDAA package (default SubtitleCast)
  -h, --help               Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --android-only)
      RUN_VIDAA=0
      ;;
    --vidaa-only)
      RUN_ANDROID=0
      ;;
    --android-variant)
      shift
      ANDROID_VARIANT="${1:-release}"
      ;;
    --vidaa-config)
      shift
      VIDAA_CONFIG="${1:-}"
      ;;
    --vidaa-output)
      shift
      VIDAA_OUTPUT="${1:-SubtitleCast}"
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      show_help
      exit 1
      ;;
  esac
  shift || true
done

if [[ ${RUN_ANDROID} -eq 0 && ${RUN_VIDAA} -eq 0 ]]; then
  echo "Nothing to do (both targets disabled)." >&2
  exit 1
fi

if [[ ${RUN_ANDROID} -eq 1 ]]; then
  if [[ ! -x "${ANDROID_SCRIPT}" ]]; then
    echo "Android build script missing or not executable: ${ANDROID_SCRIPT}" >&2
    exit 1
  fi
  "${ANDROID_SCRIPT}" "${ANDROID_VARIANT}"
fi

if [[ ${RUN_VIDAA} -eq 1 ]]; then
  if [[ ! -x "${VIDAA_SCRIPT}" ]]; then
    echo "VIDAA packaging script missing or not executable: ${VIDAA_SCRIPT}" >&2
    exit 1
  fi
  if [[ -n "${VIDAA_CONFIG}" ]]; then
    "${VIDAA_SCRIPT}" --config "${VIDAA_CONFIG}" --output "${VIDAA_OUTPUT}"
  else
    "${VIDAA_SCRIPT}" --output "${VIDAA_OUTPUT}"
  fi
fi

echo "Deployment artifacts are available in ${PROJECT_ROOT}/dist."
