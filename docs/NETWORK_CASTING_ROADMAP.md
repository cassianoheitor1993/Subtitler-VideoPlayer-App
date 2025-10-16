# Local Network Casting Roadmap

This note captures the research needed to stream the active video to other devices on the same local network using the existing VLC backend.

## Goals
- Reuse the embedded VLC instance to publish the playing media via HTTP/RTSP/Chromecast-compatible outputs.
- Keep subtitles synchronized with the outgoing stream when possible.
- Provide an intuitive UI hook (context menu / toolbar) to start and stop casting sessions.

## VLC Streaming Primer
- LibVLC exposes **stream output (`:sout`)** options that can broadcast the current media.
- Common targets:
  - `#std{access=http,mux=ts,dst=:8080}` for HTTP Transport Stream.
  - `#transcode{vcodec=h264,acodec=mp4a}:http{mux=ts,dst=:8080/}` when re-encoding is required.
  - `#duplicate{dst=display,dst=rtp{mux=ts,dst=239.255.1.1:5004}}` for multicast RTP.
- For Chromecast, VLC relies on the `renderer` API; Python bindings require discovery via `libvlc_renderer_discoverer_new` (PyQt6 wheels expose this starting in VLC 3.0+).

## Current Progress (October 2025)
- ✅ `casting_manager.py` now manages LibVLC stream output with a dedicated media player.
- ✅ Context menu and "Cast" menubar expose start/stop controls.
- ✅ Status bar displays the active stream URL while casting is running.
- ⚙️ HTTP Transport Stream is the initial supported protocol (default port `8080`).
- 🧪 Subtitles are not yet muxed into the stream; this remains future work.

## Proposed Architecture
1. **Casting Manager** (new module):
   - Holds reference to the main `vlc.Instance` to create a secondary `media_player` dedicated to streaming.
   - Accepts configuration (protocol, host, port, optional transcode parameters).
   - Provides async start/stop methods returning connection info/URL.
2. **UI Integration**:
   - Add "Cast to Network" submenu in the video context menu and main toolbar.
   - Display current streaming URL in the status bar with a quick copy button.
   - Offer presets (HTTP, RTP multicast, Chromecast) with validation of required dependencies.
3. **Subtitle Handling**:
   - When using HTTP/TCP, embed subtitles by muxing them into the stream (`:sout-all :sout-keep`).
   - For Chromecast, rely on native caption support by serving subtitles via HTTP and referencing them in the media description.
4. **Device Discovery (Stretch)**:
   - Use `zeroconf`/`pychromecast` for Chromecast detection.
   - Optionally advertise HTTP stream via mDNS using `zeroconf` so smart TVs can discover it automatically.

## Implementation Steps
- [x] Prototype a helper that takes the currently loaded media path and spawns VLC with `media.add_option(":sout=...")`.
- [x] Ensure on-screen playback continues by using a separate media player for streaming.
- [x] Surface basic start/stop controls and handle cleanup on application exit.
- [ ] Add a configuration dialog allowing the user to choose port, protocol, and transcoding recipe.
- [ ] Extend to Chromecast/UPnP once baseline HTTP streaming is stable.

## Risks & Considerations
- **Performance**: Re-encoding can be CPU intensive; offer a "passthrough" mode when the codec is already stream-friendly.
- **Firewall/Permissions**: Opening a TCP port may require firewall adjustments; document troubleshooting steps.
- **Licensing**: Some codecs (e.g., AAC) may need additional libraries on certain platforms.
- **Subtitles**: Closed captions may require conversion to VobSub or WebVTT depending on target device.

## Next Steps
- Allow the user to customise host/port/transcode settings (basic dialog + persistence).
- Investigate subtitle muxing to keep captions visible on remote players.
- Explore broadcasting via RTP/RTSP and Chromecast renderer integration.
- Consider optional mDNS advertisements for easier discovery on the LAN.
