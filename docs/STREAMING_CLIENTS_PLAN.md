# Streaming Clients Plan

This note summarizes the architecture, constraints, and prerequisites for companion apps that consume the SubtitlePlayer HTTP Transport Stream.

## Current Stream Capabilities
- Output format: MPEG-TS over HTTP (`http://<host>:8080/live.ts`).
- Video passthrough with optional transcoding in VLC; audio is passthrough or AAC depending on configuration.
- Subtitles: currently external (on-screen only). No in-stream captions.
- Latency: ~1–3 seconds depending on buffer sizes.

## Target Clients

### Android (Phone/Tablet/TV)
- Use ExoPlayer (preferred) or Android `MediaPlayer` with `MediaPlayer#setDataSource` pointing to the HTTP URL.
- Handle network permissions (`android.permission.INTERNET`).
- Provide UI for entering/remembering the streaming URL.
- Optional features: subtitle toggle (external VTT later), reconnection loop.

### Hisense VIDAA (Smart TV)
- VIDAA apps are HTML5/JavaScript packaged using VIDAA SDK.
- Use the VIDAA MediaPlayer API (based on HbbTV) to play MPEG-TS over HTTP.
- Provide simple remote-friendly UI with URL field or default to stored IP.
- Consider storing settings in localStorage for quick access.

## Networking Requirements
- Ensure SubtitlePlayer host IP is reachable (same LAN, firewall open for TCP 8080).
- For static experience, set DHCP reservation for player host or allow editing of the URL in both clients.
- Provide instructions for verifying connectivity (e.g., `curl http://<host>:8080/live.ts` should return binary data).

## Risks & Mitigations
- **Codec support**: ensure stream is H.264 + AAC for broad compatibility; configure VLC cast manager accordingly.
- **Buffer underruns**: configure clients to use small but non-zero buffer; expose retry/backoff.
- **Network changes**: implement reconnect logic upon errors.
- **Subtitles**: not currently embedded; future enhancement could expose WebVTT via separate endpoint.

## Next Steps
1. Build Android client with ExoPlayer surface view and URL entry.
2. Scaffold VIDAA HTML app using VIDAA SDK sample structure.
3. Write deployment docs (ADB install for Android, VIDAA packaging steps).
4. Extend stream configuration (optional) to enforce H.264/AAC output for maximum compatibility.
