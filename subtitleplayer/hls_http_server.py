#!/usr/bin/env python3
"""
Custom HTTP server with correct MIME types for HLS streaming.

Serves .m3u8 as application/vnd.apple.mpegurl and .ts as video/mp2t
to ensure proper playback in browsers and native HLS players.
"""

import http.server
import mimetypes
import socketserver
import sys
from pathlib import Path


# Register HLS MIME types
mimetypes.add_type("application/vnd.apple.mpegurl", ".m3u8")
mimetypes.add_type("video/mp2t", ".ts")
mimetypes.add_type("text/vtt", ".vtt")


class HLSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Request handler with CORS headers for cross-origin streaming."""
    
    def end_headers(self):
        """Add CORS headers to allow browser access."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Log with cleaner format."""
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))


def serve(port: int = 8080, directory: str = "."):
    """
    Start the HLS HTTP server.
    
    Args:
        port: Port to listen on (default 8080)
        directory: Directory to serve files from (default current)
    """
    handler = HLSRequestHandler
    
    # Change to the target directory
    target_dir = Path(directory).resolve()
    if not target_dir.exists():
        print(f"Error: Directory {target_dir} does not exist", file=sys.stderr)
        sys.exit(1)
    
    import os
    os.chdir(str(target_dir))
    
    # Use ThreadingTCPServer for concurrent connections
    with socketserver.ThreadingTCPServer(("", port), handler) as httpd:
        print(f"Serving HLS content from {target_dir} on port {port}")
        print(f"Stream URL: http://0.0.0.0:{port}/stream.m3u8")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="HLS HTTP server with proper MIME types"
    )
    parser.add_argument(
        "port",
        type=int,
        nargs="?",
        default=8080,
        help="Port to listen on (default: 8080)"
    )
    parser.add_argument(
        "-d", "--directory",
        default=".",
        help="Directory to serve (default: current directory)"
    )
    
    args = parser.parse_args()
    serve(args.port, args.directory)
