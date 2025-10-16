#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"
ANDROID_PROJECT_DIR="${PROJECT_ROOT}/clients/android/CastPlayer"
DIST_DIR="${PROJECT_ROOT}/dist/android"

if [[ ! -d "${ANDROID_PROJECT_DIR}" ]]; then
  echo "Android project directory not found: ${ANDROID_PROJECT_DIR}" >&2
  exit 1
fi

BUILD_VARIANT="${1:-release}"
BUILD_VARIANT_LOWER="${BUILD_VARIANT,,}"

case "${BUILD_VARIANT_LOWER}" in
  release)
    GRADLE_TASK="assembleRelease"
    APK_NAME="app-release.apk"
    ;;
  debug)
    GRADLE_TASK="assembleDebug"
    APK_NAME="app-debug.apk"
    ;;
  *)
    echo "Unsupported build variant: ${BUILD_VARIANT}. Use 'release' or 'debug'." >&2
    exit 1
  ;;
esac

if [[ ! -x "${ANDROID_PROJECT_DIR}/gradlew" ]]; then
  GRADLE_VERSION="8.7"
  if command -v gradle >/dev/null 2>&1; then
    echo "Gradle wrapper not found; generating one with Gradle $(gradle -v | awk '/Gradle /{print $2}' | head -n 1)..."
    (cd "${ANDROID_PROJECT_DIR}" && gradle wrapper --gradle-version "${GRADLE_VERSION}" --distribution-type all)
  else
    echo "Gradle wrapper not found; downloading Gradle ${GRADLE_VERSION} to generate one..."
    TMP_DIR="$(mktemp -d)"
    cleanup_tmp() {
      rm -rf "${TMP_DIR}"
    }
    trap cleanup_tmp EXIT

    DIST_URL="https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip"
    ARCHIVE_PATH="${TMP_DIR}/gradle-${GRADLE_VERSION}.zip"

    if command -v curl >/dev/null 2>&1; then
      curl -LsS "${DIST_URL}" -o "${ARCHIVE_PATH}"
    elif command -v wget >/dev/null 2>&1; then
      wget -q "${DIST_URL}" -O "${ARCHIVE_PATH}"
    else
      cat <<'EOF' >&2
Neither curl nor wget is available to download Gradle automatically.
Please install one of them or manually generate the wrapper by running:
  cd clients/android/CastPlayer
  gradle wrapper --gradle-version 8.7 --distribution-type all
EOF
      exit 1
    fi

    if [[ ! -s "${ARCHIVE_PATH}" ]]; then
      echo "Failed to download Gradle distribution from ${DIST_URL}." >&2
      exit 1
    fi

    if ! command -v unzip >/dev/null 2>&1; then
      echo "The 'unzip' command is required to extract Gradle." >&2
      exit 1
    fi

    unzip -q "${ARCHIVE_PATH}" -d "${TMP_DIR}"
    GRADLE_BIN_DIR="${TMP_DIR}/gradle-${GRADLE_VERSION}/bin"
    if [[ ! -x "${GRADLE_BIN_DIR}/gradle" ]]; then
      echo "Downloaded Gradle binary not found at ${GRADLE_BIN_DIR}/gradle." >&2
      exit 1
    fi

    "${GRADLE_BIN_DIR}/gradle" -p "${ANDROID_PROJECT_DIR}" wrapper --gradle-version "${GRADLE_VERSION}" --distribution-type all

    trap - EXIT
    cleanup_tmp
  fi
fi

chmod +x "${ANDROID_PROJECT_DIR}/gradlew"

pushd "${ANDROID_PROJECT_DIR}" > /dev/null
./gradlew clean "${GRADLE_TASK}"
popd > /dev/null

APK_DIR="${ANDROID_PROJECT_DIR}/app/build/outputs/apk/${BUILD_VARIANT_LOWER}"
APK_PATH="${APK_DIR}/${APK_NAME}"
if [[ ! -f "${APK_PATH}" ]]; then
  if [[ "${BUILD_VARIANT_LOWER}" == "release" && -f "${APK_DIR}/app-release-unsigned.apk" ]]; then
    echo "Signed release APK not found; using unsigned artifact. Consider signing before distribution." >&2
    APK_PATH="${APK_DIR}/app-release-unsigned.apk"
  else
    echo "Expected APK not found at ${APK_PATH}." >&2
    exit 1
  fi
fi

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "${DIST_DIR}"
OUTPUT_APK="${DIST_DIR}/CastPlayer-${BUILD_VARIANT_LOWER}-${TIMESTAMP}.apk"
cp "${APK_PATH}" "${OUTPUT_APK}"

echo "APK generated: ${OUTPUT_APK}"
