#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"
VIDAA_PROJECT_DIR="${PROJECT_ROOT}/clients/vidaa/SubtitleCast"
DIST_DIR="${PROJECT_ROOT}/dist/vidaa"

if [[ ! -d "${VIDAA_PROJECT_DIR}" ]]; then
  echo "VIDAA project directory not found: ${VIDAA_PROJECT_DIR}" >&2
  exit 1
fi

CONFIG_FILE=""
OUTPUT_BASENAME="SubtitleCast"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config)
      shift
      CONFIG_FILE="${1:-}"
      ;;
    --output)
      shift
      OUTPUT_BASENAME="${1:-SubtitleCast}"
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 [--config /path/to/config.json] [--output PackageName]" >&2
      exit 1
      ;;
  esac
  shift || true
done

if [[ -z "${CONFIG_FILE}" ]]; then
  if [[ -f "${VIDAA_PROJECT_DIR}/config.json" ]]; then
    CONFIG_FILE="${VIDAA_PROJECT_DIR}/config.json"
  elif [[ -f "${VIDAA_PROJECT_DIR}/config.template.json" ]]; then
    echo "Package config.json not found; using config.template.json. Update the template values before distributing." >&2
    CONFIG_FILE="${VIDAA_PROJECT_DIR}/config.template.json"
  else
    echo "No config.json or config.template.json found in ${VIDAA_PROJECT_DIR}." >&2
    exit 1
  fi
fi

if [[ ! -f "${CONFIG_FILE}" ]]; then
  TEMPLATE_PATH="${VIDAA_PROJECT_DIR}/config.template.json"
  if [[ -f "${TEMPLATE_PATH}" ]]; then
    echo "Configuration file not found at ${CONFIG_FILE}. Creating it from config.template.json..." >&2
    mkdir -p "$(dirname "${CONFIG_FILE}")"
    cp "${TEMPLATE_PATH}" "${CONFIG_FILE}"
  else
    echo "Configuration file does not exist: ${CONFIG_FILE}" >&2
    exit 1
  fi
fi

STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "${STAGING_DIR}"' EXIT

mkdir -p "${STAGING_DIR}/app"
cp "${CONFIG_FILE}" "${STAGING_DIR}/app/config.json"
cp "${VIDAA_PROJECT_DIR}/"*.{html,css,js} "${STAGING_DIR}/app" 2>/dev/null || true

mkdir -p "${DIST_DIR}"
OUTPUT_IPK="${DIST_DIR}/${OUTPUT_BASENAME}.ipk"

package_with_cli() {
  if command -v vidaadev >/dev/null 2>&1; then
    if vidaadev pack --project "${STAGING_DIR}/app" --out "${OUTPUT_IPK}"; then
      echo "VIDAA package generated: ${OUTPUT_IPK}"
      return 0
    else
      echo "vidaadev pack failed; falling back to zip archive." >&2
    fi
  fi
  return 1
}

package_with_zip() {
  local fallback_zip="${OUTPUT_IPK}.zip"
  (cd "${STAGING_DIR}/app" && zip -qr "${fallback_zip}" .)
  echo "Created fallback ZIP package at ${fallback_zip}. Rename to .ipk after verifying with VIDAA tools." >&2
}

if ! package_with_cli; then
  package_with_zip
fi
