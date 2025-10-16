# Subtitle Loading - Improved Robustness

## Problem
User reported that manually selected subtitles weren't being used, possibly due to filename mismatch.

## Root Cause
The original auto-load logic only checked for subtitle files with the **exact same name** as the video:
```
video.mp4 → video.srt ✅
video.mp4 → video.en.srt ❌ (not detected)
video.mp4 → movie-subtitles.srt ❌ (not detected)
```

## Solution Implemented

### 1. Enhanced Auto-Detection
Now searches for subtitles using multiple patterns:

**Priority Order:**
1. **Previously associated subtitle** (saved in config)
2. **Exact name match**: `video.srt`
3. **Language codes**: `video.en.srt`, `video.pt-BR.srt`, `video.pt.srt`, `video.es.srt`
4. **Common suffixes**: `video.eng.srt`, `video.por.srt`

**Supported Extensions:**
- `.srt` (SubRip)
- `.vtt` (WebVTT)
- `.ass` (Advanced SubStation)
- `.ssa` (SubStation Alpha)

### 2. Better Error Handling

**File Validation:**
```python
# Check if file exists
if not os.path.exists(file_path):
    show_warning("File Not Found")
    return
```

**Parse Error Feedback:**
```python
if not subtitles:
    show_warning(
        "Could not parse subtitle file\n"
        "Supported formats: SRT, VTT, ASS, SSA"
    )
```

**Exception Handling:**
```python
try:
    # Load subtitle
except Exception as e:
    show_error(f"Error: {e}")
```

### 3. Better User Feedback

**Status Messages:**
```
Before: "Loaded subtitles: video.srt"
After:  "✓ Loaded 485 subtitles from: video.srt"
```

**Console Logging:**
```python
print(f"✓ Loaded 485 subtitles from: /path/to/video.srt")
print(f"✓ Saved subtitle association: video.mp4 → video.srt")
```

**Auto-detection Logging:**
```python
print(f"Loading previously associated subtitle: video.en.srt")
print(f"Auto-detected subtitle: video.pt-BR.srt")
```

## How It Works

### Scenario 1: First Time Loading Video
```
1. User opens: movie.mp4
2. App searches for subtitles:
   - movie.srt? ❌
   - movie.en.srt? ✅ Found!
3. Auto-loads: movie.en.srt
4. Saves association: movie.mp4 → movie.en.srt
5. Status: "✓ Loaded 485 subtitles from: movie.en.srt"
```

### Scenario 2: Previously Associated Subtitle
```
1. User opens: movie.mp4 (again)
2. App checks config: movie.mp4 → movie.en.srt
3. Loads saved subtitle: movie.en.srt
4. Status: "✓ Loaded 485 subtitles from: movie.en.srt"
```

### Scenario 3: Manual Selection
```
1. User opens: movie.mp4
2. No subtitle auto-detected
3. User clicks "Load Subtitles"
4. Selects: custom-subtitle.srt
5. App loads and saves association
6. Status: "✓ Loaded 485 subtitles from: custom-subtitle.srt"
7. Next time: Auto-loads custom-subtitle.srt
```

### Scenario 4: Translated Subtitle
```
1. User translates movie.srt → movie.pt-BR.srt
2. App offers to load translated file
3. User clicks "Yes"
4. New association saved: movie.mp4 → movie.pt-BR.srt
5. Next time: Auto-loads movie.pt-BR.srt
```

## File Naming Examples

### Supported Patterns

**Exact Match:**
```
movie.mp4 → movie.srt ✅
```

**Language Codes (ISO 639-1 + Country):**
```
movie.mp4 → movie.en.srt ✅ (English)
movie.mp4 → movie.en-US.srt ✅ (English - US)
movie.mp4 → movie.pt-BR.srt ✅ (Portuguese - Brazil)
movie.mp4 → movie.pt.srt ✅ (Portuguese)
movie.mp4 → movie.es.srt ✅ (Spanish)
movie.mp4 → movie.es-LA.srt ✅ (Spanish - Latin America)
movie.mp4 → movie.fr.srt ✅ (French)
movie.mp4 → movie.de.srt ✅ (German)
```

**Common Suffixes:**
```
movie.mp4 → movie.eng.srt ✅
movie.mp4 → movie.por.srt ✅
```

**Not Auto-Detected (but work if manually loaded):**
```
movie.mp4 → subtitles.srt ⚠️ (different name)
movie.mp4 → movie-subs.srt ⚠️ (suffix added)
movie.mp4 → movie_subtitles.srt ⚠️ (different format)
```

### Translation Output Names
When translating subtitles, files are saved as:
```
movie.srt → movie.pt-BR.srt (Portuguese Brazil)
movie.srt → movie.en-US.srt (English US)
movie.srt → movie.es-ES.srt (Spanish Spain)
movie.srt → movie.zh-CN.srt (Chinese Simplified)
```

These are **automatically detected** on next load! ✅

## Configuration Storage

Subtitle associations are saved in:
```
~/.subtitleplayer/config.json
```

Format:
```json
{
  "subtitle_files": {
    "/path/to/movie.mp4": "/path/to/movie.en.srt",
    "/path/to/video.avi": "/path/to/custom-subs.srt"
  }
}
```

## User Experience

### Before
```
User: Loads video.mp4
App: No subtitle found (even though video.en.srt exists)
User: Manually loads video.en.srt
App: Works, but...
User: Closes and reopens video
App: No subtitle again! 😡
User: Must manually load every time
```

### After
```
User: Loads video.mp4
App: Auto-detects video.en.srt ✅
Status: "✓ Loaded 485 subtitles from: video.en.srt"
User: Closes and reopens video
App: Loads video.en.srt automatically ✅
Status: "✓ Loaded 485 subtitles from: video.en.srt"
User: Happy! 😊
```

## Debugging

### Check Console Output

When loading a video, look for:
```
Loading previously associated subtitle: movie.en.srt
✓ Loaded 485 subtitles from: /home/user/Videos/movie.en.srt
✓ Saved subtitle association: movie.mp4 → movie.en.srt
```

Or for auto-detection:
```
Auto-detected subtitle: movie.pt-BR.srt
✓ Loaded 485 subtitles from: /home/user/Videos/movie.pt-BR.srt
✓ Saved subtitle association: movie.mp4 → movie.pt-BR.srt
```

### Check Status Bar

Bottom of window shows:
```
✓ Loaded 485 subtitles from: movie.en.srt
```

Number (485) confirms subtitles are actually loaded.

### Error Messages

**File Not Found:**
```
Subtitle file not found:
/path/to/missing.srt
```

**Parse Error:**
```
Could not parse subtitle file:
corrupted.srt

Supported formats: SRT, VTT, ASS, SSA
```

**General Error:**
```
An error occurred while loading subtitles:
[error details]
```

## Troubleshooting

### Subtitle Not Auto-Loading

**Check filename:**
```bash
# Video file
movie.mp4

# Subtitle file (in same directory)
movie.srt          ✅ Will auto-load
movie.en.srt       ✅ Will auto-load
movie.pt-BR.srt    ✅ Will auto-load
subtitles.srt      ❌ Won't auto-load (different name)
movie-subs.srt     ❌ Won't auto-load (suffix)
```

**Solution:** Rename subtitle to match video:
```bash
mv subtitles.srt movie.srt
```

Or use "Load Subtitles" button to manually select.

### Subtitle Loads But Doesn't Display

**Possible causes:**
1. Subtitle timing offset incorrect
2. Subtitle color same as background
3. Subtitle position off-screen
4. Font size too small

**Solution:** Open "Subtitle Settings" and adjust.

### Wrong Subtitle Loaded

**Example:**
```
Video: movie.mp4
Subtitles in folder:
- movie.srt (English)
- movie.pt-BR.srt (Portuguese)

Auto-loads: movie.srt
Want: movie.pt-BR.srt
```

**Solution:**
1. Click "Load Subtitles" button
2. Select `movie.pt-BR.srt`
3. New association saved
4. Next time: Auto-loads `movie.pt-BR.srt`

### Subtitle Association Lost

Config file might be corrupted or deleted.

**Fix:**
```bash
# Check config
cat ~/.subtitleplayer/config.json

# If corrupted, remove
rm ~/.subtitleplayer/config.json

# Restart app (creates new config)
```

Then reload subtitles manually (associations will be saved).

## Code Changes

### Enhanced load_subtitle Method
```python
def load_subtitle(self, file_path: str):
    try:
        # Validate file exists
        if not os.path.exists(file_path):
            show_warning("File Not Found")
            return
        
        # Parse
        subtitles = parser.parse_file(file_path)
        
        if subtitles:
            # Apply timing
            # Save association
            # Show status with count
            status.show(f"✓ Loaded {len(subtitles)} subtitles")
        else:
            show_warning("Parse Error")
    
    except Exception as e:
        show_error(f"Error: {e}")
```

### Improved Auto-Detection
```python
# Priority search
patterns = [
    video.srt,              # Exact match
    video.en.srt,           # Language code
    video.pt-BR.srt,        # Language + region
    video.eng.srt,          # Common suffix
    ...
]

for pattern in patterns:
    if exists(pattern):
        load_subtitle(pattern)
        break
```

## Benefits

### User Benefits
- ✅ Subtitles auto-load with language codes
- ✅ Better error messages
- ✅ Subtitle count shown in status
- ✅ Console logging for debugging
- ✅ More filename patterns supported

### Developer Benefits
- ✅ Better error handling
- ✅ Debug output for troubleshooting
- ✅ Extensible pattern matching
- ✅ Cleaner code structure

## Summary

**Before:**
- Only exact filename matches
- Poor error feedback
- No debug output
- Unclear if subtitles loaded

**After:**
- Multiple filename patterns
- Clear error messages
- Console logging
- Subtitle count in status
- Better user experience

The subtitle loading is now **much more robust** and will work with common subtitle naming conventions! 🎉

## Related Files
- `src/video_player.py` - Subtitle loading logic
- `src/config_manager.py` - Subtitle association storage
- `src/subtitle_parser.py` - Subtitle file parsing
