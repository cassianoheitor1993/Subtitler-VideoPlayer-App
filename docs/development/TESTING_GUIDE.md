# 🧪 Testing Guide for SubtitlePlayer

## Quick Start - Using VS Code Debugger

### **Method 1: Press F5** (Recommended)
1. Open VS Code in the SubtitlePlayer directory
2. Press **`F5`** to start debugging
3. Select "SubtitlePlayer: Run Application" if prompted
4. Application launches with debugger attached!

### **Method 2: Debug Panel**
1. Press **`Ctrl+Shift+D`** to open Debug panel
2. Select **"SubtitlePlayer: Run Application"** from dropdown
3. Click the green Play button (or press F5)
4. Watch the Debug Console for output

### **Method 3: Command Line**
```bash
cd /home/cmedeiros/Documents/Cassiano-Portfolio/Subtitler-App/SubtitlePlayer
/home/cmedeiros/Documents/Cassiano-Portfolio/.venv/bin/python src/video_player.py
```

---

## 🎯 What to Test

### **1. Basic Video Playback** ✅

**Steps:**
1. Launch SubtitlePlayer
2. Click **"Open Video"** button
3. Select a video file (MP4, MKV, AVI, etc.)
4. Video should start playing

**Expected Results:**
- ✅ Video loads and plays smoothly
- ✅ Audio is synchronized
- ✅ Controls respond (Play/Pause/Stop)
- ✅ Timeline slider moves with playback
- ✅ Volume slider adjusts audio

**Console Check:**
- ❌ Should NOT see VLC error floods
- ✅ Should see minimal, clean output

---

### **2. Click-to-Seek Timeline** ✨ (NEW v1.1)

**Steps:**
1. Load and play a video
2. Click anywhere on the timeline slider
3. Video should jump to that position instantly

**Expected Results:**
- ✅ Clicking works while playing or paused
- ✅ Instant jump, no dragging needed
- ✅ Subtitle timing adjusts correctly

---

### **3. Double-Click Fullscreen** ✨ (NEW v1.1)

**Steps:**
1. Load and play a video
2. Double-click on the video frame (black area)
3. Should enter fullscreen mode
4. Double-click again to exit

**Expected Results:**
- ✅ Enters fullscreen smoothly
- ✅ Controls still accessible
- ✅ ESC or double-click exits fullscreen

---

### **4. Right-Click Context Menu** ✨ (NEW v1.1)

**Steps:**
1. Load a video
2. Right-click on the video frame
3. Context menu should appear

**Expected Results:**
- ✅ Menu shows all options:
  - ▶/⏸ Play/Pause
  - ⏹ Stop
  - ⛶ Fullscreen
  - 📄 Load Subtitle File
  - ⬇ Download Subtitles
  - ⚙ Subtitle Settings
  - 🤖 Generate Subtitles (AI)
- ✅ All actions work from menu

---

### **5. Subtitle Download (OpenSubtitles)** 📥

**Steps:**
1. Load a movie/TV show video
2. Click **"Download Subtitles"**
3. Search dialog appears
4. Enter movie name or let it auto-detect
5. Select language
6. Click Search
7. Select a subtitle from results
8. Click Download

**Expected Results:**
- ✅ Search works (API connection successful)
- ✅ Results appear with ratings
- ✅ Download saves subtitle file
- ✅ Subtitles load automatically
- ✅ Subtitles display on video

**Note:** Requires OpenSubtitles API key (see API_KEY_INFO.md)

---

### **6. Load Local Subtitle File** 📂

**Steps:**
1. Load a video
2. Click **"Load Subtitle"**
3. Select a .srt, .vtt, or .ass file
4. Subtitle should load

**Expected Results:**
- ✅ File dialog opens
- ✅ Subtitle parses correctly
- ✅ Subtitles display in sync with video
- ✅ Timing is accurate

---

### **7. Subtitle Customization** ⚙️

**Steps:**
1. Load video with subtitles
2. Click **"Subtitle Settings"**
3. Modify settings:
   - Font family, size
   - Text color
   - Background color/opacity
   - Outline color/width
   - Position (vertical)
   - Timing offset
4. Click Apply

**Expected Results:**
- ✅ Changes apply instantly
- ✅ Preview shows changes
- ✅ Settings persist per video
- ✅ Can reset to defaults

---

### **8. AI Subtitle Generation** 🤖 (NEW v1.1)

**Prerequisites:**
- FFmpeg installed: `ffmpeg -version`
- AI dependencies: Check with button or see requirements-full.txt

**Steps:**
1. Load a video with audio
2. Press **Ctrl+G** or Right-click → "Generate Subtitles (AI)"
3. AI Generation Dialog appears
4. Select language (or Auto-detect)
5. Select model size:
   - **Tiny**: Ultra-fast, lower accuracy
   - **Base**: ⭐ Recommended balance
   - **Small**: Better quality
   - **Medium**: Professional
   - **Large**: Best quality
6. Click **"Generate Subtitles"**
7. Watch **Processing Log** section
8. Wait for completion (30s-5min depending on model/video)
9. Review preview
10. Click **"Save & Use"**

**Expected Results:**
- ✅ Dependencies detected correctly
- ✅ Model downloads (first time only, 75MB-3GB)
- ✅ **Processing Log shows:**
  ```
  [14:35:10] 📹 Extracting audio from video...
  [14:35:13] ✓ Audio extracted (3s)
  [14:35:13] 🤖 Transcribing with Whisper (base model on GPU (CUDA))...
  [14:35:15] ⏳ This may take a while, please be patient...
  [14:35:45] ✓ Transcription complete (30s)
  [14:35:46] 📝 Processing subtitle segments...
  [14:35:47] ✓ Generation complete! 142 segments created
  ```
- ✅ Progress bar updates
- ✅ Preview shows first 10 subtitle lines
- ✅ Subtitles save to .srt file
- ✅ Subtitles load automatically
- ✅ Quality is good (95-99% accurate depending on model)

**Performance Notes:**
- GPU (CUDA): ~3-10s per minute of video
- CPU only: ~30-120s per minute of video

---

### **9. Keyboard Shortcuts** ⌨️

Test these shortcuts:

| Shortcut | Action |
|----------|--------|
| **Space** | Play/Pause |
| **F** | Toggle Fullscreen |
| **Ctrl+O** | Open Video |
| **Ctrl+S** | Subtitle Settings |
| **Ctrl+D** | Download Subtitles |
| **Ctrl+G** | Generate AI Subtitles |
| **M** | Mute/Unmute |
| **↑/↓** | Volume Up/Down |
| **←/→** | Seek Backward/Forward |

**Expected Results:**
- ✅ All shortcuts respond correctly
- ✅ No conflicts with system shortcuts

---

### **10. Multi-Video Workflow** 🎬

**Steps:**
1. Load Video A, customize subtitles
2. Close video
3. Load Video B, customize differently
4. Close video
5. Re-load Video A

**Expected Results:**
- ✅ Video A subtitle settings restored
- ✅ Each video remembers its own settings
- ✅ Settings persist across app restarts

---

## 🐛 Debugging Features

### **Set Breakpoints**
1. Open `src/video_player.py`
2. Click left of line number to set red dot
3. Run debugger (F5)
4. Execution pauses at breakpoint
5. Inspect variables in Debug panel

### **Watch Variables**
1. While debugging, hover over variables
2. Right-click → "Add to Watch"
3. Monitor value changes

### **Debug Console**
- Type Python expressions
- Inspect objects
- Call functions

### **Call Stack**
- See function call hierarchy
- Click to jump to specific frame

---

## 🔍 What to Check in Console

### **Good Output (Clean):**
```
Starting SubtitlePlayer...
Video loaded: /path/to/video.mp4
Subtitles loaded: 142 entries
```

### **Bad Output (Issues):**
```
Error: Failed to load video
Traceback: ...
ModuleNotFoundError: ...
```

---

## ⚠️ Known Non-Issues

These are **normal** and can be ignored:

### **VLC Audio Warnings** (Suppressed)
If you still see these (rare), they're harmless:
- "main audio output error: too low audio sample frequency"
- "chain filter error: Too high level of recursion"
- "main filter error: Failed to create video converter"

**Why:** VLC testing different audio/video codecs, finds working one eventually

### **AI Model Download** (First Time)
- Base model: ~150MB download
- Takes 30-120 seconds
- Only happens once

---

## 🎯 Success Criteria

Your SubtitlePlayer is working correctly if:

- ✅ Video plays smoothly
- ✅ Audio synchronized
- ✅ All buttons respond
- ✅ Timeline clicking works
- ✅ Double-click fullscreen works
- ✅ Right-click menu appears
- ✅ Subtitles download/load
- ✅ Subtitle customization works
- ✅ Settings persist per video
- ✅ AI generation works (with deps)
- ✅ Processing log shows progress
- ✅ Console output is clean
- ✅ No crashes or freezes

---

## 🆘 Troubleshooting

### **Issue: Video won't load**
**Solution:**
- Check VLC is installed: `vlc --version`
- Install codecs: `sudo apt install ubuntu-restricted-extras`

### **Issue: No subtitles showing**
**Solution:**
- Check subtitle file is loaded (statusbar shows filename)
- Verify timing offset in Subtitle Settings
- Check subtitle color isn't same as video background

### **Issue: AI generation fails**
**Solution:**
```bash
# Install dependencies
sudo apt install ffmpeg
pip install openai-whisper torch torchvision torchaudio

# Check installation
python -c "import whisper; import torch; print('OK')"
```

### **Issue: Debugger won't start**
**Solution:**
1. Check Python extension installed
2. Verify interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Choose: `/home/cmedeiros/Documents/Cassiano-Portfolio/.venv/bin/python`

### **Issue: Slow performance**
**Solution:**
- Close other applications
- Use smaller AI models (tiny/base)
- Check GPU support: `python -c "import torch; print(torch.cuda.is_available())"`

---

## 📊 Performance Benchmarks

### **Video Playback:**
- CPU usage: 10-30%
- RAM: 200-400MB
- Should handle 4K video smoothly

### **AI Generation (Base Model):**
- GPU: ~3-5 seconds per minute of video
- CPU: ~30-60 seconds per minute of video
- RAM: ~1-2GB during generation

---

## ✅ Final Checklist

Before considering testing complete:

- [ ] Video playback works
- [ ] All UX features tested (click timeline, double-click, context menu)
- [ ] Subtitle download works
- [ ] Subtitle loading works
- [ ] Subtitle customization works
- [ ] Settings persist correctly
- [ ] AI generation works (or install instructions clear)
- [ ] Processing log shows detailed progress
- [ ] Keyboard shortcuts work
- [ ] Console output is clean
- [ ] Debugger can start successfully
- [ ] No critical errors in console
- [ ] Performance is acceptable

---

## 🎉 Ready for Production!

If all tests pass, your SubtitlePlayer is:
- ✅ Feature-complete
- ✅ Production-ready
- ✅ Well-debugged
- ✅ User-friendly
- ✅ Professional quality

**Next:** Build snap package and publish to Ubuntu App Store! 📦

---

**Last Updated:** October 15, 2025
**Version:** 1.1.0+debug
**Status:** Testing Phase
