# SubtitlePlayer

A professional, feature-rich video player for Linux with intelligent subtitle management, AI-powered subtitle generation, and network streaming capabilities.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)
![VLC](https://img.shields.io/badge/VLC-Required-orange.svg)

## ✨ Key Features

### 🎬 Video Playback
- **Multi-format Support**: MP4, AVI, MKV, MOV, FLV, WMV, M4V, WebM, and more
- **Hardware Acceleration Controls**: Switch between Auto, VA-API, NVDEC, VDPAU, or CPU-only decoding from the Playback menu
- **Proxy Generation**: Create lightweight 1080p H.264 proxies for high-bitrate or 4K sources without leaving the player
- **Interactive Timeline**: Click to seek, smooth playback controls
- **Recent Files**: Quick access to previously watched videos

### � Subtitle Management
- **Native Subtitle Download**: Search and download subtitles directly from OpenSubtitles.com
- **Auto-load Subtitles**: Automatically finds and loads subtitle files in the same directory
- **Smart Metadata**: Remembers subtitle preferences per video

### 🎨 Customizable Styling
- **Typography**: Font family, size, bold, italic
- **Colors**: Text color, stroke color and width, semi-transparent backgrounds
- **Position**: Top/center/bottom, left/center/right alignment
- **Margins**: Adjustable vertical and horizontal spacing
- **Live Preview**: See changes instantly while watching
- **Per-Video Settings**: Saves your preferences for each video

### 🤖 AI Subtitle Generation
- **Whisper AI Integration**: Generate subtitles for videos without them
- **99+ Languages**: Support for virtually any language
- **Automatic Detection**: Language auto-detection capability
- **High Accuracy**: State-of-the-art transcription quality

### 🌍 Translation System
- **18+ Languages**: English, Portuguese, Spanish, Chinese, French, German, and more
- **File-based**: Creates new subtitle files (e.g., `movie.pt-BR.srt`)
- **Progress Visualization**: Real-time progress bar with percentage
- **Cancelable**: Stop translation at any time (UI awaits safe shutdown if you close mid-process)
- **Background Friendly**: Minimize the dialog and monitor progress from the status footer
- **Batch Processing**: Translate entire subtitle files efficiently

### 📊 Status Footer Dashboard
- **Inline Task Monitor**: Background AI, translation, and casting tasks appear as chips in the status bar
- **One-click Restore**: Reopen background dialogs (AI generator, translation, analytics) directly from the footer
- **Quick Cancel**: Stop long-running jobs without reopening the original window
- **Auto-cleanup**: Completed tasks fade out automatically to keep the UI tidy

### 🛰️ Network Streaming (Beta)
- **HLS Streaming**: Cast video + subtitles to other devices
- **Cross-platform**: Works with Android, iOS, browsers, smart TVs
- **1080p Quality**: H.264 High Profile with AAC audio
- **Subtitle Burn-in**: Optional subtitle embedding in stream

- **Low Latency**: Configurable segment duration for responsiveness
- **Low Latency**: Configurable segment duration for responsiveness

### ⌨️ Keyboard Shortcuts
- **ESC**: Exit fullscreen
- **F**: Toggle fullscreen
- **Space**: Play/pause
- **←/→**: Seek backward/forward
- **↑/↓**: Volume up/down
- **S**: Open subtitle search
- **O**: Open video file

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Getting Started](docs/guides/QUICKSTART.md)** - Quick installation and usage guide
- **[Features Documentation](docs/features/)** - Detailed feature explanations
- **[Development Guide](docs/development/)** - For contributors and developers
- **[Deployment](docs/deployment/)** - Publishing and distribution
- **[User Guides](docs/guides/)** - AI subtitles, API setup, and more

## 🚀 Quick Start

### Prerequisites
- **FFmpeg**: Required for generating 1080p proxy files (optional but recommended)

### Installation
- **Ctrl+Alt+P**: Generate 1080p proxy of the current video
git clone https://github.com/cassianoheitor1993/Subtitler-VideoPlayer-App.git SubtitlePlayer
cd SubtitlePlayer

# Run the automated setup
./run.sh
```

The `run.sh` script will:
1. Create a virtual environment
2. Install all Python dependencies
3. Launch the application

### Get OpenSubtitles API Key

1. Go to [https://www.opensubtitles.com](https://www.opensubtitles.com)
2. Create a free account
3. Go to [https://www.opensubtitles.com/api](https://www.opensubtitles.com/api)
4. Generate your free API key
5. Save it - you'll enter it when first searching for subtitles

See [API Key Setup Guide](docs/guides/API_KEY_INFO.md) for detailed instructions.

## 📖 Usage

### Launching the App

```bash
# Simple - just run:
./run.sh

# Or use Python directly:
python3 main.py
```

### Basic Workflow

1. **Open a Video**: File → Open Video (or `Ctrl+O`)
2. **Load Subtitles**:
   - Auto-loads matching `.srt` files from the video directory
   - **Manual**: File → Load Subtitles (`Ctrl+S`)
   - **Download**: Subtitle → Download (`Ctrl+D`)
   - **AI Generate**: Subtitle → Generate with AI
3. **Customize**: View → Subtitle Settings (modern sidebar or legacy dialog)
4. **Translate**: Subtitle → Translate Subtitles
   - Minimize the legacy dialog to keep working and use the status footer chip to reopen or cancel
5. **Cast**: Cast → Start HTTP Cast (stream to other devices)

#### Performance Tools
- **Hardware Acceleration Profiles**: `Playback → Hardware Acceleration` lets you force Auto detection, Intel/AMD VA-API, NVIDIA NVDEC, legacy VDPAU, or fall back to CPU-only decoding. Toggle options on the fly; playback resumes at the same position.
- **Generate 1080p Proxy**: Use `Playback → Generate 1080p Proxy...` (or `Ctrl+Alt+P`) to create a lighter H.264 copy of the current video for smoother playback. Progress appears in the status footer; click the resulting 🎬 chip to open the proxy once it finishes.

#### Translation Tips
- The dialog can be closed safely once the footer chip shows completion; closing mid-process will ask to cancel first.
- If you confirm cancellation, the dialog hides until the translator shuts down gracefully.
- Partial results can be saved when cancellations occur—the footer message reflects success or failure.

#### AI Subtitle Generation
- Use the “⬇ Minimize” button to run Whisper in the background while you keep browsing videos.
- The `🤖` chip in the status footer shows live progress and provides reopen/cancel shortcuts.
- Completed jobs remain accessible from the chip until you dismiss or reopen the dialog.

### Network Casting

Cast your video with embedded subtitles to any device on your network:

1. Load a video with subtitles
2. **Cast → Start HTTP Cast**
3. Share the URL with other devices:
   - **Android/iOS**: Open in VLC or MX Player
   - **Browsers**: Works in Chrome, Firefox, Safari
   - **Smart TVs**: Use the VIDAA client app
4. **Cast → Stop Cast** to end the stream

**Technical Details**:
- Output: 1080p H.264 High Profile (Level 4.1) + AAC stereo
- Format: HLS (HTTP Live Streaming)
- Compatibility: All modern devices with HLS support
- Latency: 2-second segments (configurable)
- Logs: Check `logs/cast_failures/` if issues occur

See [Streaming Documentation](docs/features/STREAMING_FIX_COMPLETE.md) for advanced configuration.

## 🏗️ Repository Structure

```
SubtitlePlayer/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── CODE_OF_CONDUCT.md          # Community guidelines
├── CONTRIBUTING.md             # Contribution guidelines
│
├── run.sh                       # Quick launcher script
├── main.py                      # Application entry point
├── launch.py                    # Alternative launcher
│
├── requirements.txt             # Core dependencies
├── requirements-full.txt        # All dependencies (including AI)
│
├── src/                         # Source code
│   ├── video_player.py          # Main player window
│   ├── subtitle_settings_sidebar.py  # Modern sidebar UI
│   ├── opensubtitles_api.py     # OpenSubtitles API client
│   ├── subtitle_parser.py       # Subtitle format parser
│   ├── ffmpeg_casting_manager.py    # HLS streaming manager
│   ├── hls_http_server.py       # Custom HTTP server for HLS
│   ├── debug_logger.py          # Streaming analytics
│   └── ...                      # Additional modules
│
├── docs/                        # Documentation
│   ├── README.md                # Documentation index
│   ├── guides/                  # User guides
│   ├── features/                # Feature documentation
│   ├── development/             # Development docs
│   └── deployment/              # Publishing guides
│
├── tests/                       # Test suites
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
│
├── scripts/                     # Utility scripts
│   ├── install.sh               # Installation script
│   └── push-to-github.sh        # Git helper
│
├── tools/                       # Development tools
│   ├── quick_cast_test.py       # HLS streaming tester
│   └── verify_installation.py  # Installation verifier
│
├── clients/                     # Client applications
│   ├── android/                 # Android CastPlayer app
│   └── vidaa/                   # Smart TV client
│
├── assets/                      # Icons and resources
├── config/                      # Configuration files
├── logs/                        # Application logs
├── resources/                   # Assets and data files
└── temp/                        # Temporary files
```

## 🧪 Testing

```bash
# Run all tests
python3 -m pytest

# Run specific test suite
python3 -m pytest tests/unit/

# With coverage report
python3 -m pytest --cov=src tests/
```

See [Testing Guide](docs/development/TESTING_GUIDE.md) for more details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit with clear messages: `git commit -m "Add amazing feature"`
5. Push to your fork: `git push origin feature/amazing-feature`
6. Open a Pull Request

## 📋 Configuration

Configuration files are stored in `~/.subtitleplayer/`:

- `config.json`: Application settings (API key, preferences)
- `recent_files.json`: Recently played videos
- `metadata/`: Per-video subtitle preferences
- `cache/`: Downloaded subtitles cache

## 🗺️ Roadmap

- [ ] Playlist support
- [ ] Picture-in-picture mode
- [ ] Subtitle synchronization tool
- [ ] Cloud subtitle storage
- [ ] Browser extension integration
- [ ] macOS and Windows support

See [Improvements](docs/development/IMPROVEMENTS.md) for the full roadmap.

## ⚖️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **VLC**: Powerful multimedia framework
- **OpenSubtitles**: Comprehensive subtitle database
- **OpenAI Whisper**: State-of-the-art speech recognition
- **PyQt6**: Modern UI framework
- **FFmpeg**: Multimedia processing toolkit

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/cassianoheitor1993/Subtitler-VideoPlayer-App/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cassianoheitor1993/Subtitler-VideoPlayer-App/discussions)
- **Documentation**: [docs/](docs/README.md)

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---


---

**Made with ❤️ for the Linux community**

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
