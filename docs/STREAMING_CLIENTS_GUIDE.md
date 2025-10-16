# Companion Streaming Clients Guide

This guide explains how to build and deploy the Android and Hisense VIDAA apps that consume the SubtitlePlayer HTTP transport stream (`http://<host>:8080/live.ts`).

## 1. Prepare the SubtitlePlayer Host
1. Ensure the casting manager is running and reachable on the LAN.
2. Prefer H.264 video + AAC audio for maximum device compatibility. If necessary, enable transcoding in `casting_manager.py` before starting the stream.
3. Confirm an external client can reach the stream:
   ```bash
   curl -I http://10.0.0.59:8080/live.ts
   ```
   The command should return an HTTP 200 with `Content-Type: video/MP2T`.

## 2. Android Client (Subtitle Cast)
### Prerequisites
- Android Studio Jellyfish (or newer).
- Android SDK Platform 34 installed.
- Physical device (Android 7.0+) or emulator on the same network.

### Build Steps
1. Open Android Studio → *Open an Existing Project* → select `clients/android/CastPlayer`.
2. Let Gradle sync. The project uses Kotlin, AGP 8.5.2, and Media3 ExoPlayer.
3. Connect a device with USB debugging or configure a Wi-Fi debugging session.
4. Click **Run ▶** to install and launch the app.

#### Automated build
Use the helper script to produce a signed (debug or release) APK without opening Android Studio:
```bash
./scripts/build-android-client.sh release
```
Artifacts are stored in `dist/android/` with a timestamped filename.
The script downloads Gradle automatically when neither `gradle` nor `gradlew` is present (requires `curl` or `wget`, plus `unzip`).

### Usage
1. Enter the stream URL (defaults to `http://10.0.0.59:8080/live.ts`).
2. Tap **Play** to begin playback. Tap **Stop** to end.
3. The last used URL is stored in `SharedPreferences` for convenience.
4. The app includes the HTTP Live Streaming extension; if you later expose an HLS playlist, simply change the URL.

### Optional Adjustments
- Increase buffer size by extending `LoadControl` configuration before building the player.
- Add subtitle support once SubtitlePlayer serves WebVTT; use `MediaItem.SubtitleConfiguration`.

### Signing the APK for distribution
1. Create or locate your release keystore. To generate a new one:
   ```bash
   keytool -genkeypair -v \
     -keystore /secure/location/subtitleplayer-release.jks \
     -alias subtitleplayer \
     -keyalg RSA -keysize 2048 -validity 3650
   ```
2. Export the keystore password and alias credentials (or plan to enter them when prompted):
   ```bash
   export KEYSTORE_PASSWORD="<keystore-password>"
   export KEY_PASSWORD="<key-password-if-different>"
   ```
3. Sign the APK using the helper script:
   ```bash
   ./scripts/sign-android-apk.sh \
     --keystore /secure/location/subtitleplayer-release.jks \
     --alias subtitleplayer \
     --input dist/android/CastPlayer-release-<timestamp>.apk \
     --output dist/android/CastPlayer-release-signed.apk
   ```
4. Verify the APK before shipping:
   ```bash
   apksigner verify --print-certs dist/android/CastPlayer-release-signed.apk
   ```

## 3. VIDAA TV Client (Subtitle Cast)
### Prerequisites
- VIDAA ADK / SDK installed (obtain from the Hisense developer portal).
- VIDAA TV in Developer Mode connected to the same network.
- Optional helper: after downloading the ADK archive, run `./scripts/install-vidaadev.sh --archive /path/to/VIDAA_ADK.zip` to extract it and expose the `vidaadev` CLI in your PATH.

### Build Steps
1. Copy `clients/vidaa/SubtitleCast` into your VIDAA workspace.
2. Create a `config.json` describing the app. A starter template is provided at `clients/vidaa/SubtitleCast/config.template.json`.
3. Run the VIDAA packer:
   ```bash
   vidaadev pack --project SubtitleCast --out SubtitleCast.ipk
   ```
4. Deploy to the TV using the VIDAA developer tools or via USB, depending on model/firmware.

#### Automated packaging
Package the web app (with optional config override) using the helper script:
```bash
./scripts/package-vidaa-client.sh --config clients/vidaa/SubtitleCast/config.json
```
If the VIDAA CLI is unavailable, the script creates a ZIP fallback at `dist/vidaa/SubtitleCast.ipk.zip` for manual processing. When the specified `config.json` is missing, it is generated from `config.template.json` automatically so you can adjust metadata before publishing.

#### Post-install verification
After installing the official ADK and exposing `vidaadev`, rerun the helper to produce a native `.ipk`:
```bash
./scripts/package-vidaa-client.sh --config clients/vidaa/SubtitleCast/config.json --output SubtitleCast
```
The script now detects the CLI and emits `dist/vidaa/SubtitleCast.ipk`. You can confirm availability with `vidaadev --version` before packaging.

### Usage
- Launch the "Subtitle Cast" app on the TV.
- Enter or confirm the stream URL and press **OK** on the remote (or the on-screen button).
- Press **Back/Return** to stop playback. The app remembers the last URL in `localStorage`.

### Notes
- The HTML5 `<video>` element expects MPEG-TS; ensure the stream matches (H.264/AAC recommended).
- VIDAA remote key codes may differ slightly by model; adjust in `app.js` if needed.
- For 4K streams, verify the TV can decode the chosen bitrate and codec profile.

## 4. Troubleshooting
| Issue | Android Fix | VIDAA Fix |
|-------|-------------|-----------|
| Stream downloads instead of playing | Ensure ExoPlayer is used (already handled) | Update SubtitlePlayer to send `Content-Type: video/MP2T` |
| Buffering / stutter | Enable VLC transcoding with smaller bitrate, or enlarge player buffer | Reduce stream bitrate; consider wired Ethernet |
| No audio | Transcode to AAC | Same as Android |
| Cannot connect | Check firewall / IP address; confirm both devices share LAN | Same; also ensure TV DNS resolves host |

## 5. Future Enhancements
- Serve WebVTT subtitles alongside the TS stream and load them on clients.
- Offer QR code in SubtitlePlayer to simplify connecting new devices.
- Transition to HLS or DASH for native browser compatibility if needed.

## 6. Combined automation
To build both clients in one shot (and customise variants), run:
```bash
./scripts/deploy-clients.sh
```
Use `--android-only` or `--vidaa-only` to target a specific platform. All artifacts land under `dist/`.
