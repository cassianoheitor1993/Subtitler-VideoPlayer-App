# Subtitle Cast for VIDAA

A minimal HTML5 application for Hisense VIDAA TVs that plays the SubtitlePlayer HTTP transport stream.

## Features
- Input/remember stream URL (stored in `localStorage`).
- Remote shortcuts: **OK** to play, **Back** to stop.
- Works with default HTML5 video element in VIDAA Web App SDK.

## Packaging with VIDAA SDK
1. Install the VIDAA App Developer Kit (ADK) from the Hisense developer portal.
2. Copy this folder into your ADK workspace.
3. Create the required `config.json` (if packaging) describing app metadata. A starter is available as `config.template.json` (and is auto-copied by the helper script if `config.json` is missing):
   ```json
   {
     "appId": "com.subtitleplayer.cast",
     "type": "web",
     "title": "Subtitle Cast",
     "version": "1.0.0",
     "entry": "index.html",
     "resolution": "1920x1080"
   }
   ```
4. Use the `vidaadev pack` command (or the GUI packer) to produce the `.ipk` package. You can also run `../../../scripts/package-vidaa-client.sh` from the repo root to stage the package automatically (requires the CLI for full `.ipk` output, otherwise a `.ipk.zip` fallback is created). If you need to expose the `vidaadev` CLI, run `../../../scripts/install-vidaadev.sh --archive /path/to/VIDAA_ADK.zip` after downloading the official ADK.
5. Deploy to the TV via VIDAA Developer Mode or USB depending on model.

## Notes
- Ensure the SubtitlePlayer host is reachable from the TV; use the LAN IP (e.g. `http://10.0.0.59:8080/live.ts`).
- The video element expects MPEG-TS (H.264/AAC). Adjust SubtitlePlayer to transcode when necessary.
- If buffering is excessive, consider using HLS segments instead of raw TS in the future.
