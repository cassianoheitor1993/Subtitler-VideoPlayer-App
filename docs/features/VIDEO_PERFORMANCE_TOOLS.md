# Video Performance Tools

This guide explains the controls available in SubtitlePlayer to improve playback when working with demanding sources such as high bitrate 4K files.

## Hardware Acceleration Profiles

SubtitlePlayer exposes VLC's decoding backends so you can pick the driver that matches your GPU or fall back to CPU-only decoding when needed.

- **Location**: `Playback → Hardware Acceleration`
- **Options**:
  - `Auto (Detect GPU)`: Let VLC pick any available hardware decoder.
  - `Intel/AMD VA-API`: Forces the VA-API backend, recommended for most modern Intel iGPUs and AMD cards on Linux.
  - `NVIDIA NVDEC`: Uses NVIDIA's video decode engine (requires proprietary drivers).
  - `Legacy VDPAU`: Targets older NVIDIA/AMD hardware that still relies on VDPAU.
  - `Disabled (CPU only)`: Disables hardware acceleration entirely.
- **Behavior**: Switching profiles restarts the VLC media player internally, preserves the current playback position, and stores your choice in `~/.subtitleplayer/config.json` for subsequent sessions.

Use this menu if the default setting causes dropped frames or codec errors.

## 1080p Proxy Generation

When hardware decoding is not enough, create a lightweight proxy copy for smooth playback while keeping the original file untouched.

- **Location**: `Playback → Generate 1080p Proxy...` or press `Ctrl+Alt+P`.
- **Requirements**: FFmpeg must be available in your shell `PATH`.
- **Output**: H.264/AVC video at 1080p (height), AAC audio at 192 kbps, with `+faststart` enabled for responsive seeking. Proxies are saved next to the source file using the `_1080p_proxy` suffix.
- **Progress & Control**:
  - Progress appears as a 🎬 chip in the status footer and in the floating task indicators.
  - The chip's cancel button lets you stop the transcode safely; partial files are removed automatically.
  - When the proxy is ready, click the 🎬 chip or select the notification to load the optimized file instantly.

### Workflow Tips

1. Load the original high bitrate video.
2. If playback stutters, try a different hardware profile first.
3. If stuttering persists, trigger the 1080p proxy generation and continue browsing while it runs.
4. Use the status footer to open the proxy once the task finishes. The original file remains selected in the recent files list if you need to switch back.

These tools give you quick recovery paths for problematic encodes without leaving SubtitlePlayer or running manual FFmpeg commands.
