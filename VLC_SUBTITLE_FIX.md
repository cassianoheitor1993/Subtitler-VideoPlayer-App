# VLC Internal Subtitle Rendering Fix

## Problem
When users manually selected a Portuguese subtitle (`.pt-BR.srt`), the application correctly:
- Loaded the Portuguese subtitle file
- Saved the association in config
- Displayed confirmation messages

However, **English subtitles still appeared on screen** despite Portuguese being selected.

## Root Cause
**VLC was rendering embedded English subtitles from the video file itself**, while the application was only managing external `.srt` files. VLC's internal subtitle rendering was never disabled, causing it to display embedded subtitle tracks that override our custom subtitle overlay.

## Solution
Disabled VLC's internal subtitle rendering in three ways:

### 1. VLC Instance Arguments (`src/video_player.py` lines 123-130)
```python
vlc_args = [
    '--no-xlib',
    '--quiet',
    '--no-video-title-show',
    '--avcodec-hw=none',
    '--no-sub-autodetect-file',  # Don't auto-detect subtitle files
    '--sub-track=-1',  # Disable embedded subtitle tracks
]
```

- `--no-sub-autodetect-file`: Prevents VLC from automatically loading subtitle files in the video directory
- `--sub-track=-1`: Disables any embedded subtitle tracks in the video file

### 2. Explicit SPU Disable (`src/video_player.py` line 462)
```python
def load_video(self, file_path: str):
    # ...
    media = self.instance.media_new(file_path)
    self.media_player.set_media(media)
    
    # Disable VLC's internal subtitle rendering (we handle subtitles ourselves)
    self.media_player.video_set_spu(-1)
```

The `video_set_spu(-1)` method explicitly disables VLC's subtitle (SPU = SubPicture Unit) rendering when a video loads.

### 3. Improved Logging
Added clearer logging to help debug subtitle loading:
```python
print(f"[Subtitle] Loading saved association: {os.path.basename(subtitle_file)}")
print(f"[Subtitle] Auto-detected: {sub_path.name}")
```

## Technical Details

### What is SPU (SubPicture Unit)?
- VLC's internal mechanism for rendering subtitles and overlays
- Handles both embedded subtitle tracks (in MKV, MP4, etc.) and external subtitle files
- Operates independently of our custom PyQt6 subtitle overlay

### Why Multiple Disable Methods?
- **Instance args** (`--sub-track=-1`): Global configuration for the VLC instance
- **`video_set_spu(-1)`**: Per-video setting when loading media
- **`--no-sub-autodetect-file`**: Prevents automatic subtitle file detection

Using all three ensures maximum compatibility across different VLC versions and video formats.

## Testing
1. Load a video with embedded English subtitles
2. Manually select a Portuguese `.pt-BR.srt` file
3. Verify that **only Portuguese subtitles** appear
4. Check console output for `[Subtitle] Loading saved association: ...pt-BR.srt`
5. Reload the video to confirm association persists

## Result
✅ VLC's internal subtitle rendering is now fully disabled  
✅ Only our custom subtitle overlay displays  
✅ Manual subtitle selection works correctly  
✅ Embedded video subtitle tracks are ignored  

## Files Modified
- `src/video_player.py` (lines 123-130, 462)

## Impact
- **No breaking changes** - Only disables VLC's internal rendering
- **Performance**: Neutral (VLC was already decoding subtitles)
- **Compatibility**: Works with all video formats and subtitle types
- **User Experience**: Subtitles now display as expected when manually selected

---

**Date**: 2025-01-24  
**Issue**: Portuguese subtitle selected but English displays  
**Solution**: Disable VLC's internal subtitle rendering (SPU)
