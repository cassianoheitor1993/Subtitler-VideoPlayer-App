#!/bin/bash

# Script to create a desktop entry for SubtitlePlayer
# This makes the application appear in the Linux application menu

APP_NAME="SubtitlePlayer"
APP_EXEC="$(pwd)/run.sh"
APP_ICON="$(pwd)/subtitleplayer/resources/icon.png" # Assuming there is an icon here
DESKTOP_FILE="$HOME/.local/share/applications/subtitleplayer.desktop"

# Check if run.sh exists
if [ ! -f "$APP_EXEC" ]; then
    echo "❌ Error: run.sh not found in current directory."
    exit 1
fi

# Try to find an icon
if [ ! -f "$APP_ICON" ]; then
    # Fallback to any png in resources or assets
    APP_ICON=$(find "$(pwd)" -name "*.png" | head -n 1)
fi

echo "Creating desktop entry at: $DESKTOP_FILE"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.1
Type=Application
Name=$APP_NAME
GenericName=Video Player
Comment=Professional video player with subtitle download and AI generation
Icon=$APP_ICON
Exec=$APP_EXEC %F
Terminal=false
Categories=AudioVideo;Video;Player;Qt;
MimeType=video/x-msvideo;video/mp4;video/mpeg;video/x-matroska;video/webm;video/quicktime;video/x-flv;video/x-ms-wmv;
Keywords=video;player;subtitles;media;movie;film;clip;
StartupNotify=true
StartupWMClass=SubtitlePlayer
EOF

chmod +x "$DESKTOP_FILE"

echo "✓ Desktop entry created successfully!"
echo "You can now find SubtitlePlayer in your application menu."
