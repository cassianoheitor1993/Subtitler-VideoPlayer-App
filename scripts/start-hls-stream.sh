#!/bin/bash
#
# Start FFmpeg HLS streaming + Python HTTP server
# This bypasses VLC's broken HTTP streaming module
#

set -e

VIDEO_PATH="$1"
if [ -z "$VIDEO_PATH" ]; then
    echo "Usage: $0 <video_path>"
    exit 1
fi

if [ ! -f "$VIDEO_PATH" ]; then
    echo "Error: Video file not found: $VIDEO_PATH"
    exit 1
fi

# Setup
HLS_DIR="/tmp/subtitle_player_hls"
PORT=8080

echo "Setting up HLS streaming..."
mkdir -p "$HLS_DIR"

# Kill any existing processes
pkill -f "ffmpeg.*hls.*stream.m3u8" 2>/dev/null || true
pkill -f "http.server $PORT" 2>/dev/null || true
sleep 1

# Start FFmpeg HLS encoder in background
echo "Starting FFmpeg HLS encoder..."
ffmpeg -re -stream_loop -1 \
    -i "$VIDEO_PATH" \
    -c copy \
    -f hls \
    -hls_time 2 \
    -hls_list_size 5 \
    -hls_flags delete_segments+append_list \
    -hls_segment_filename "$HLS_DIR/segment%03d.ts" \
    "$HLS_DIR/stream.m3u8" \
    </dev/null >/dev/null 2>&1 &

FFMPEG_PID=$!
echo "FFmpeg PID: $FFMPEG_PID"

# Wait for first segment
echo "Waiting for stream to initialize..."
for i in {1..10}; do
    if [ -f "$HLS_DIR/stream.m3u8" ]; then
        break
    fi
    sleep 1
done

if [ ! -f "$HLS_DIR/stream.m3u8" ]; then
    echo "Error: Stream failed to initialize"
    kill $FFMPEG_PID 2>/dev/null || true
    exit 1
fi

# Start HTTP server
echo "Starting HTTP server on port $PORT..."
cd "$HLS_DIR"
python3 -m http.server $PORT </dev/null >/dev/null 2>&1 &
HTTP_PID=$!

echo "HTTP server PID: $HTTP_PID"
sleep 2

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "✓ Streaming active!"
echo ""
echo "Stream URL for mobile device:"
echo "  http://$LOCAL_IP:$PORT/stream.m3u8"
echo ""
echo "To stop streaming:"
echo "  kill $FFMPEG_PID $HTTP_PID"
echo ""
echo "PIDs saved to /tmp/subtitle_player_stream.pids"
echo "$FFMPEG_PID $HTTP_PID" > /tmp/subtitle_player_stream.pids

# Keep script alive
wait $FFMPEG_PID $HTTP_PID
