#!/usr/bin/env python3
"""Helper script to exercise the FFmpeg casting pipeline and inspect codec output."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ffmpeg_casting_manager import (  # type: ignore[import-not-found]
    FFmpegCastingConfig,
    FFmpegCastingManager,
)


DEFAULT_VIDEO = Path("temp/sample.mp4")
PROFILE_PATH = PROJECT_ROOT / "config" / "quick_cast_profile.json"
HLS_DIR = Path("/tmp/subtitle_player_hls")
DEFAULT_SEGMENT = HLS_DIR / "segment000.ts"


def _load_media_profile() -> tuple[Path, Path | None]:
    video_path = DEFAULT_VIDEO
    subtitle_path: Path | None = None

    if PROFILE_PATH.exists():
        try:
            data = json.loads(PROFILE_PATH.read_text())
            raw_video = data.get("video")
            raw_subtitle = data.get("subtitle")
            if raw_video:
                candidate = Path(str(raw_video)).expanduser()
                video_path = candidate
            if raw_subtitle:
                candidate = Path(str(raw_subtitle)).expanduser()
                subtitle_path = candidate
        except Exception as exc:  # pragma: no cover - defensive parsing
            print(f"Warning: failed to read {PROFILE_PATH}: {exc}", file=sys.stderr)

    return video_path, subtitle_path


def _persist_media_profile(video: Path, subtitle: Path | None) -> None:
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "video": str(video.expanduser().resolve()),
        "subtitle": str(subtitle.expanduser().resolve()) if subtitle else None,
    }
    PROFILE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


PROFILE_VIDEO, PROFILE_SUBTITLE = _load_media_profile()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start a temporary HLS cast, wait for the first segment, and dump ffprobe details.",
    )
    parser.add_argument(
        "--video",
        type=Path,
        default=PROFILE_VIDEO,
        help=f"Path to the source video (default: {PROFILE_VIDEO})",
    )
    parser.add_argument(
        "--subtitle",
        type=Path,
        default=PROFILE_SUBTITLE,
        help="Optional subtitle file to burn into the stream.",
    )
    parser.add_argument(
        "--startup-timeout",
        type=int,
        default=60,
        help="Seconds to wait for the manifest and first segment before giving up (default: 60).",
    )
    parser.add_argument(
        "--segment",
        type=Path,
        default=DEFAULT_SEGMENT,
        help=f"HLS segment to inspect with ffprobe (default: {DEFAULT_SEGMENT}).",
    )
    parser.add_argument(
        "--save-profile",
        action="store_true",
        help="Persist the provided video/subtitle paths for future runs.",
    )
    parser.add_argument(
        "--keep-alive",
        action="store_true",
        help="Keep the HLS stream running after verification (press Ctrl+C to stop).",
    )
    return parser.parse_args()


def ensure_path_exists(path: Path, kind: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"{kind} not found: {resolved}")
    return resolved


def run_ffprobe(segment_path: Path) -> str:
    cmd = [
        "ffprobe",
        "-hide_banner",
        "-loglevel",
        "error",
        "-show_streams",
        "-print_format",
        "json",
        str(segment_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:  # pragma: no cover - depends on FFmpeg installation
        raise RuntimeError("ffprobe not found. Please install FFmpeg tools.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffprobe failed: {exc.stderr.strip() or exc}") from exc

    return result.stdout.strip()


def wait_for_segment(segment_path: Path, timeout: int) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if segment_path.exists() and segment_path.stat().st_size > 0:
            return
        time.sleep(0.5)
    raise TimeoutError(f"Timed out waiting for segment: {segment_path}")


def main() -> int:
    args = parse_args()

    try:
        video_path = ensure_path_exists(args.video, "Video")
        subtitle_path = ensure_path_exists(args.subtitle, "Subtitle") if args.subtitle else None
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.save_profile:
        try:
            _persist_media_profile(video_path, subtitle_path)
            print(f"Saved quick cast profile to {PROFILE_PATH}")
        except Exception as exc:  # pragma: no cover - filesystem errors
            print(f"Failed to save quick cast profile: {exc}", file=sys.stderr)

    config = FFmpegCastingConfig(startup_timeout=args.startup_timeout)
    manager = FFmpegCastingManager()

    print(f"Starting cast for {video_path}")
    if subtitle_path:
        print(f"Burning subtitles from {subtitle_path}")

    cleanup_needed = True
    try:
        url = manager.start_hls_stream(
            str(video_path),
            config=config,
            subtitle_path=str(subtitle_path) if subtitle_path else None,
        )
        print(f"Stream URL: {url}")

        try:
            wait_for_segment(args.segment, timeout=max(10, args.startup_timeout))
        except TimeoutError as exc:
            print(exc, file=sys.stderr)
            return 3

        size = args.segment.stat().st_size
        print(f"Segment ready: {args.segment} ({size} bytes)")

        try:
            ffprobe_output = run_ffprobe(args.segment)
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 4

        print("ffprobe output:")
        print(ffprobe_output)
        print(f"Manifest is available at: {url}")
        print("Open this URL on your target device to verify playback.")
        if args.keep_alive:
            print("Keeping stream alive. Press Ctrl+C to stop.")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Received interrupt, stopping stream...")
            manager.stop()
            cleanup_needed = False
        return 0
    finally:
        if cleanup_needed:
            manager.stop()
            print("Casting stopped.")


if __name__ == "__main__":
    raise SystemExit(main())
