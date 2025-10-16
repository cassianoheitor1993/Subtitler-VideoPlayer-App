#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: install-vidaadev.sh --archive /path/to/VIDAA_ADK.zip [--install-dir ~/VIDAA_ADK] [--symlink ~/.local/bin]

Installs the official VIDAA ADK CLI (vidaadev) from a downloaded archive.

Arguments:
  --archive PATH       (required) Path to the VIDAA ADK archive obtained from the Hisense developer portal.
  --install-dir DIR    Directory where the archive will be extracted (default: ~/VIDAA_ADK).
  --symlink DIR        Directory in which to create a vidaadev symlink (default: ~/.local/bin).
  -h, --help           Show this help text and exit.

The script does not download the ADK—obtain it manually from https://developers.vidaa.com before running.
EOF
}

ARCHIVE=""
INSTALL_DIR="${HOME}/VIDAA_ADK"
SYMLINK_DIR="${HOME}/.local/bin"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive)
      shift
      ARCHIVE="${1:-}"
      ;;
    --install-dir)
      shift
      INSTALL_DIR="${1:-}"
      ;;
    --symlink)
      shift
      SYMLINK_DIR="${1:-}"
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

if [[ -z "${ARCHIVE}" ]]; then
  echo "Error: --archive is required." >&2
  show_help
  exit 1
fi

if [[ ! -f "${ARCHIVE}" ]]; then
  echo "Error: archive not found at ${ARCHIVE}" >&2
  exit 1
fi

mkdir -p "${INSTALL_DIR}"
INSTALL_DIR="$(cd "${INSTALL_DIR}" && pwd)"

EXT="${ARCHIVE##*.}"
LOWER_ARCHIVE="${ARCHIVE,,}"

if [[ "${LOWER_ARCHIVE}" == *.tar.gz || "${LOWER_ARCHIVE}" == *.tgz ]]; then
  if ! command -v tar >/dev/null 2>&1; then
    echo "The 'tar' command is required to extract ${ARCHIVE}." >&2
    exit 1
  fi
  tar -xzf "${ARCHIVE}" -C "${INSTALL_DIR}"
elif [[ "${LOWER_ARCHIVE}" == *.zip ]]; then
  if ! command -v unzip >/dev/null 2>&1; then
    echo "The 'unzip' command is required to extract ${ARCHIVE}." >&2
    exit 1
  fi
  unzip -q "${ARCHIVE}" -d "${INSTALL_DIR}"
else
  echo "Unsupported archive format: ${ARCHIVE}" >&2
  exit 1
fi

VIDAA_BIN=""
while IFS= read -r -d '' candidate; do
  if [[ -x "${candidate}" ]]; then
    VIDAA_BIN="${candidate}"
    break
  fi
done < <(find "${INSTALL_DIR}" -type f -name vidaadev -print0)

if [[ -z "${VIDAA_BIN}" ]]; then
  echo "Could not locate the vidaadev binary in ${INSTALL_DIR}." >&2
  echo "Search manually and adjust the script or PATH." >&2
  exit 1
fi

echo "Found vidaadev at ${VIDAA_BIN}" >&2

mkdir -p "${SYMLINK_DIR}"
SYMLINK_DIR="$(cd "${SYMLINK_DIR}" && pwd)"
SYMLINK_PATH="${SYMLINK_DIR}/vidaadev"

ln -sf "${VIDAA_BIN}" "${SYMLINK_PATH}"

echo "Created symlink at ${SYMLINK_PATH}" >&2

echo "Add ${SYMLINK_DIR} to your PATH if not already present, e.g.:" >&2
echo "  echo 'export PATH=\"${SYMLINK_DIR}:\$PATH\"' >> ~/.bashrc" >&2
echo "  echo 'export PATH=\"${SYMLINK_DIR}:\$PATH\"' >> ~/.zshrc" >&2
echo "Then reload your shell (source the file or open a new terminal)." >&2

echo "Installation complete. Test with: vidaadev --version" >&2
