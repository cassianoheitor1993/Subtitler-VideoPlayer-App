# Subtitle Display Fix - October 15, 2025

## Problem
Subtitles were being loaded correctly but not displaying on screen. Console logs showed:
- ✓ Loaded 1842 subtitles from Portuguese file
- Overlay widget initialized  
- But no subtitles visible on video

## Root Causes & Fixes

### 1. **Time Calculation Error** (PRIMARY)
**Issue**: `update_ui()` was calculating subtitle time incorrectly
```python
# WRONG (was dividing twice):
current_time = self.media_player.get_time() // 1000  # Already in seconds
# ...
current_time / 1000.0  # Divided by 1000 AGAIN! → microseconds
```

**Fix**: Properly handle VLC's time in milliseconds
```python
# RIGHT:
current_time_ms = self.media_player.get_time()  # milliseconds
current_time_float = current_time_ms / 1000.0  # seconds (for subtitle lookup)
```

### 2. **Subtitle Overlay Not Visible** (CRITICAL)
**Issue**: `SubtitleOverlay` widget was created but **never shown**
- Widget created with `SubtitleOverlay(self.video_frame)`
- Geometry set to `(0, 0, 1200, 600)`
- **`.show()` was never called** → widget remained invisible
- Result: paintEvent never triggered

**Fix**: Added `.show()` to make overlay visible
```python
self.subtitle_overlay = SubtitleOverlay(self.video_frame)
self.subtitle_overlay.setGeometry(0, 0, 1200, 600)
self.subtitle_overlay.show()  # ← THIS WAS MISSING
self.subtitle_overlay.raise_()
```

### 3. **Z-Order Management**
Ensured overlay stays on top with `raise_()` calls in both:
- Initial creation
- Window resize events

## Code Changes

### `src/video_player.py`

**Change 1: Subtitle overlay visibility (lines 168-176)**
- Removed unused `video_layout` variable
- Added `.show()` to make overlay visible
- Kept `.raise_()` to ensure overlay is on top

**Change 2: Time calculation fix (lines 640-658)**
- Clearly separated milliseconds vs. seconds handling
- Added intermediate variables for clarity
- Fixed double-division bug in subtitle time lookup

## Testing Results
✅ Subtitles now display correctly on screen  
✅ Portuguese subtitles showing proper text (e.g., "Desculpe", "Ah, com licença")  
✅ Text updates as video plays  
✅ Overlay responds to video position changes  
✅ Widget resizing works correctly  

## Console Output Verification
```
[Subtitle] Loading saved association: Final.Destination...pt-BR.srt
✓ Loaded 1842 subtitles from: ...pt-BR.srt
[Overlay] Setting subtitle: Desculpe....  ← Subtitles being set
[Overlay] paintEvent called!               ← Paint event triggering
[Overlay] Widget size: 640x480             ← Correct dimensions
```

## Impact
- ✅ Subtitles now display on video
- ✅ Manual subtitle selection works
- ✅ Portuguese/English language switching works
- ✅ Subtitle timing synchronized with video
- 🔄 No performance impact (visibility and rendering already working)

---

**Issue Type**: Critical Display Bug  
**Status**: ✅ FIXED  
**Files Modified**: `src/video_player.py`  
**Commit**: Subtitle overlay visibility and time calculation fixes
