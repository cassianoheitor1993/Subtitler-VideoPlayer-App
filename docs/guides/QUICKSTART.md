# Quick Start Guide

## Getting Started in 5 Minutes

### Step 1: Install Dependencies (2 minutes)

Open a terminal and run:

```bash
cd ~/Documents/SubtitlePlayer
chmod +x install.sh
./install.sh
```

The installation script will:
- ✓ Check for Python 3
- ✓ Check for VLC (and offer to install it)
- ✓ Create virtual environment
- ✓ Install all Python packages

### Step 2: Get Your API Key (1 minute)

1. Visit: https://www.opensubtitles.com/api
2. Sign up for a free account (if you don't have one)
3. Click "Generate New Key"
4. Copy your API key (looks like: `AbCdEfGh1234567890`)

**Important**: Keep this key safe! You'll need it to download subtitles.

### Step 3: Launch the Player (30 seconds)

```bash
./run.sh
```

Or double-click `run.sh` in your file manager.

### Step 4: Play Your First Video (1 minute)

1. Click **"Open Video"** button
2. Select a video file from your computer
3. Video starts playing! 🎬

### Step 5: Download Subtitles (30 seconds)

1. While video is playing, click **"Download Subtitles"**
2. Paste your API key (first time only)
3. Subtitles are automatically searched
4. Select your preferred subtitle
5. Click **"Download Selected"**
6. Subtitles appear on video! 🎉

## Common Tasks

### Customize Subtitle Appearance
- Click **"Subtitle Settings"**
- Change font, size, color, position
- See live preview
- Click **"Apply"**

### Adjust Subtitle Timing
If subtitles are out of sync:
1. Click **"Subtitle Settings"**
2. Find "Time Offset"
3. Use positive value if subtitles are late
4. Use negative value if subtitles are early
5. Adjust by 0.1-second increments

### Keyboard Shortcuts
- `Space`: Play/Pause
- `F`: Fullscreen
- `Ctrl+O`: Open video
- `Ctrl+S`: Load subtitle file
- `Ctrl+D`: Download subtitles
- `Ctrl+Q`: Quit

## Tips & Tricks

### Auto-load Subtitles
Name your subtitle file the same as your video:
```
Movie.mp4
Movie.srt  ← Loads automatically!
```

### Best Subtitle Settings for Readability
- **Font Size**: 24-32 pt
- **Text Color**: White (#FFFFFF)
- **Stroke Color**: Black (#000000)
- **Stroke Width**: 2-3 px
- **Background**: Semi-transparent black
- **Position**: Bottom, 50px margin

### Find Subtitles by Movie Name
If video hash doesn't work:
1. In Download Subtitles dialog
2. Enter movie/show name in "Search" field
3. Select language
4. Click "Search"

## Troubleshooting

### "VLC not found" error
```bash
# Ubuntu/Debian/Mint
sudo apt install vlc libvlc-dev

# Fedora
sudo dnf install vlc vlc-devel

# Arch
sudo pacman -S vlc
```

### Subtitles not showing
- Check status bar (shows loaded subtitle file)
- Try adjusting timing offset
- Verify subtitle file format (SRT, VTT, ASS)

### Can't download subtitles
- Verify API key is correct
- Check internet connection
- Free accounts: 5 downloads per day limit

## Need Help?

- Read the full README.md
- Check the error message in terminal
- Verify all dependencies are installed

---

**You're ready to enjoy movies with perfect subtitles! 🎬✨**
