#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: sign-android-apk.sh --keystore /path/keystore.jks --alias KEY_ALIAS --input dist/android/CastPlayer-release-*.apk [--output signed.apk]

Options:
  --keystore PATH       Path to the Java keystore (JKS or PKCS12) containing the signing key (required)
  --alias NAME          Alias of the key entry inside the keystore (required)
  --input PATH          Unsigned APK to sign (required)
  --output PATH         Destination for the signed APK (default: append -signed before .apk)
  --storepass-env VAR   Environment variable holding the keystore password (default: KEYSTORE_PASSWORD)
  --keypass-env VAR     Environment variable holding the key password (default: KEY_PASSWORD; falls back to keystore password)
  --help                Show this message

Passwords are read from the specified environment variables when set. If missing, you will be prompted securely.
EOF
}

KEYSTORE=""
ALIAS=""
INPUT_APK=""
OUTPUT_APK=""
STOREPASS_ENV="KEYSTORE_PASSWORD"
KEYPASS_ENV="KEY_PASSWORD"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keystore)
      shift
      KEYSTORE="${1:-}"
      ;;
    --alias)
      shift
      ALIAS="${1:-}"
      ;;
    --input)
      shift
      INPUT_APK="${1:-}"
      ;;
    --output)
      shift
      OUTPUT_APK="${1:-}"
      ;;
    --storepass-env)
      shift
      STOREPASS_ENV="${1:-KEYSTORE_PASSWORD}"
      ;;
    --keypass-env)
      shift
      KEYPASS_ENV="${1:-KEY_PASSWORD}"
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

if [[ -z "${KEYSTORE}" || -z "${ALIAS}" || -z "${INPUT_APK}" ]]; then
  echo "Missing required arguments." >&2
  show_help
  exit 1
fi

if [[ ! -f "${INPUT_APK}" ]]; then
  echo "Input APK not found: ${INPUT_APK}" >&2
  exit 1
fi

if [[ ! -f "${KEYSTORE}" ]]; then
  echo "Keystore not found: ${KEYSTORE}" >&2
  exit 1
fi

if [[ -z "${OUTPUT_APK}" ]]; then
  if [[ "${INPUT_APK}" == *.apk ]]; then
    OUTPUT_APK="${INPUT_APK%.apk}-signed.apk"
  else
    OUTPUT_APK="${INPUT_APK}-signed.apk"
  fi
fi

STOREPASS="${!STOREPASS_ENV:-}"
if [[ -z "${STOREPASS}" ]]; then
  read -r -s -p "Enter keystore password: " STOREPASS
  echo
fi

KEYPASS="${!KEYPASS_ENV:-}"
if [[ -z "${KEYPASS}" ]]; then
  KEYPASS="${STOREPASS}"
fi

ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-}}"
APKSIGNER=""
ZIPALIGN=""

if command -v apksigner >/dev/null 2>&1; then
  APKSIGNER="$(command -v apksigner)"
fi

if [[ -z "${APKSIGNER}" && -n "${ANDROID_SDK_ROOT}" ]]; then
  if [[ -d "${ANDROID_SDK_ROOT}/build-tools" ]]; then
    LATEST_BUILD_TOOLS="$(ls -1 "${ANDROID_SDK_ROOT}/build-tools" | sort -V | tail -n1)"
    if [[ -n "${LATEST_BUILD_TOOLS}" && -x "${ANDROID_SDK_ROOT}/build-tools/${LATEST_BUILD_TOOLS}/apksigner" ]]; then
      APKSIGNER="${ANDROID_SDK_ROOT}/build-tools/${LATEST_BUILD_TOOLS}/apksigner"
    fi
    if [[ -x "${ANDROID_SDK_ROOT}/build-tools/${LATEST_BUILD_TOOLS}/zipalign" ]]; then
      ZIPALIGN="${ANDROID_SDK_ROOT}/build-tools/${LATEST_BUILD_TOOLS}/zipalign"
    fi
  fi
fi

if [[ -z "${APKSIGNER}" ]]; then
  echo "Could not locate apksigner. Ensure it is in PATH or set ANDROID_SDK_ROOT." >&2
  exit 1
fi

if [[ -z "${ZIPALIGN}" ]]; then
  if command -v zipalign >/dev/null 2>&1; then
    ZIPALIGN="$(command -v zipalign)"
  fi
fi

TMP_ALIGNED="${INPUT_APK%.apk}-aligned.apk"
if [[ -n "${ZIPALIGN}" ]]; then
  echo "Aligning APK with zipalign..."
  "${ZIPALIGN}" -f -p 4 "${INPUT_APK}" "${TMP_ALIGNED}"
else
  echo "zipalign not found; skipping alignment step." >&2
  cp "${INPUT_APK}" "${TMP_ALIGNED}"
fi

trap 'rm -f "${TMP_ALIGNED}"' EXIT

echo "Signing APK..."
"${APKSIGNER}" sign \
  --ks "${KEYSTORE}" \
  --ks-key-alias "${ALIAS}" \
  --ks-pass "pass:${STOREPASS}" \
  --key-pass "pass:${KEYPASS}" \
  --out "${OUTPUT_APK}" \
  "${TMP_ALIGNED}"

echo "Verifying signature..."
"${APKSIGNER}" verify --verbose "${OUTPUT_APK}"

echo "Signed APK written to ${OUTPUT_APK}"
