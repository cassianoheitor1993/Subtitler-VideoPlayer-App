# SubtitlePlayer

A professional video player for Linux with native subtitle download support through OpenSubtitles.com API.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## Features

- 🎬 **Multi-format Video Support**: Play .mp4, .avi, .mkv, .mov, .flv, .wmv, .m4v, .webm, and more
- 📥 **Native Subtitle Download**: Search and download subtitles directly from OpenSubtitles.com
- 🎨 **Customizable Subtitle Styling**: 
  - Font family, size, bold, italic
  - Text color, stroke color, and width
  - Background color and transparency
  - Position (top/center/bottom, left/center/right)
  - Timing offset adjustment
- 🎯 **Live Timing Preview**: See exactly which subtitle appears at your adjusted timing offset in real-time
- 🌍 **Multi-language Translation**: Translate subtitles to 18+ languages including English, Portuguese, Spanish, Chinese, French, German, and more
- 🤖 **AI Subtitle Generation**: Generate subtitles using Whisper AI for videos without subtitles (99+ languages)
- 💾 **Smart Metadata Management**: Saves subtitle preferences per video
- 🌙 **Modern Dark Theme**: Professional, eye-friendly interface
- ⌨️ **Keyboard Shortcuts**: Quick access to common functions (ESC, F, Space, etc.)
- 📂 **Recent Files**: Easy access to previously played videos
- 🎯 **Auto-load Subtitles**: Automatically finds and loads subtitle files
- 🖱️ **Interactive Timeline**: Click to seek, double-click for fullscreen
- 📱 **Right-click Context Menu**: Quick access to common actions

## Screenshots

### Main Player Interface
- Clean, modern video player with playback controls
- Real-time subtitle display with customizable styling
- Timeline with precise time display

### Subtitle Search Dialog
- Search OpenSubtitles.com by video hash or movie name
- Filter by language
- View subtitle details (downloads, ratings, format)
- One-click download to video directory

### Subtitle Settings
- Comprehensive styling options
- Live preview of changes
- Save preferences per video

## Requirements

- **Operating System**: Linux (Ubuntu, Linux Mint, Debian, Fedora, etc.)
- **Python**: 3.8 or higher
- **VLC**: VLC media player must be installed

## Installation

### 1. Install System Dependencies

#### Ubuntu/Debian/Linux Mint:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv vlc libvlc-dev
```

#### Fedora:
```bash
sudo dnf install python3 python3-pip vlc vlc-devel
```

#### Arch Linux:
```bash
sudo pacman -S python python-pip vlc
```

### 2. Clone or Download the Project

```bash
cd ~/Documents
git clone <repository-url> SubtitlePlayer
cd SubtitlePlayer
```

Or download and extract the ZIP file to your desired location.

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Get OpenSubtitles API Key

1. Go to [https://www.opensubtitles.com](https://www.opensubtitles.com)
2. Create a free account
3. Go to [https://www.opensubtitles.com/api](https://www.opensubtitles.com/api)
4. Generate your free API key
5. Save it - you'll need it when searching for subtitles

## Usage

### Running the Application

#### From Terminal:
```bash
cd ~/Documents/SubtitlePlayer
source venv/bin/activate
python3 main.py
```

#### Using the Launcher Script:
```bash
chmod +x run.sh
./run.sh
```

### Basic Workflow

1. **Open a Video**:
   - Click "Open Video" button or use `Ctrl+O`
   - Browse and select your video file
   - Video starts playing automatically

2. **Load Subtitles**:
   
   **Option A - Auto-load**:
   - If a subtitle file (.srt, .vtt, .ass) with the same name exists in the video directory, it loads automatically
   
   **Option B - Manual Load**:
   - Click "Load Subtitles" or press `Ctrl+S`
   - Select subtitle file from your computer
   
   **Option C - Download from OpenSubtitles**:
   - Click "Download Subtitles" or press `Ctrl+D`
   - Enter your API key (first time only)
   - Subtitles are automatically searched by video hash
   - Select desired subtitle from results
   - Click "Download Selected"
   - Subtitle downloads to video directory and loads automatically

3. **Customize Subtitle Appearance**:
   - Click "Subtitle Settings"
   - Adjust font, colors, position, timing
   - See live preview of changes
   - Click "Apply" to save

4. **Playback Controls**:
   - **Space**: Play/Pause
   - **F**: Toggle fullscreen
   - **Ctrl+O**: Open video
   - **Ctrl+S**: Load subtitle file
   - **Ctrl+D**: Download subtitles
   - **Ctrl+Q**: Quit application

## Configuration

Configuration files are stored in `~/.subtitleplayer/`:

- `config.json`: Application settings (API key, preferences)
- `recent_files.json`: List of recent videos
- `metadata/`: Per-video subtitle preferences

## File Structure

```
SubtitlePlayer/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── run.sh                 # Launcher script
├── README.md              # This file
├── src/
│   ├── video_player.py           # Main player window
│   ├── opensubtitles_api.py      # OpenSubtitles API client
│   ├── subtitle_parser.py        # Subtitle format parser
│   ├── subtitle_search_dialog.py # Subtitle search UI
│   ├── subtitle_settings_dialog.py # Settings UI
│   └── config_manager.py         # Configuration management
├── assets/                # Icons and resources
└── resources/             # Additional resources
```

## Supported Formats

### Video Formats:
- MP4, AVI, MKV, MOV, FLV, WMV, M4V, WEBM
- Any format supported by VLC

### Subtitle Formats:
- SRT (SubRip)
- VTT (WebVTT)
- ASS/SSA (Advanced SubStation Alpha)

## Troubleshooting

### VLC Not Found
**Error**: `ImportError: No module named 'vlc'`

**Solution**:
```bash
# Install VLC
sudo apt install vlc libvlc-dev  # Ubuntu/Debian
sudo dnf install vlc vlc-devel   # Fedora

# Reinstall python-vlc
pip install --upgrade python-vlc
```

### Qt Platform Plugin Error
**Error**: `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"`

**Solution**:
```bash
sudo apt install python3-pyqt6  # Use system PyQt6
# Or
pip install PyQt6 --force-reinstall
```

### Subtitle Not Displaying
1. Check if subtitle file is loaded (status bar shows filename)
2. Verify subtitle timing isn't out of sync
3. Adjust timing offset in Subtitle Settings
4. Check subtitle position isn't off-screen

### OpenSubtitles Download Fails
1. Verify API key is correct
2. Check internet connection
3. Ensure you haven't exceeded rate limits (5 downloads/day for free accounts)
4. Try searching by movie name instead of hash

## Desktop Launcher (Optional)

Create a desktop entry for easy access:

```bash
cat > ~/.local/share/applications/subtitleplayer.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SubtitlePlayer
Comment=Professional Video Player with Subtitle Support
Exec=/home/$USER/Documents/SubtitlePlayer/run.sh
Icon=video-player
Terminal=false
Categories=AudioVideo;Video;Player;
EOF
```

Update desktop database:
```bash
update-desktop-database ~/.local/share/applications
```

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License.

## Credits

- **VLC**: Video playback powered by VLC media player
- **OpenSubtitles**: Subtitle database and API
- **PyQt6**: GUI framework

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation

## Roadmap

Future enhancements:
- [ ] Playlist support
- [ ] Drag-and-drop file loading
- [ ] Audio track selection
- [ ] Playback speed control
- [ ] Bookmark/chapter support
- [ ] Screenshot capture
- [ ] Video filters and effects
- [ ] Subtitle editor
- [ ] Multiple subtitle track support
- [ ] Cloud subtitle backup

---

**Enjoy your movies with perfect subtitles! 🎬🎉**
