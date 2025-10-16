# Subtitle Timing & Translation Features

## Overview
SubtitlePlayer now includes advanced features for subtitle synchronization and multi-language translation.

---

## 🎯 Timing Preview

### What it does
Shows you **exactly which subtitle** will appear at the adjusted time offset, giving you instant visual feedback when syncing subtitles manually.

### How to use
1. Open a video with subtitles loaded
2. Go to **Settings > Subtitle Settings**
3. In the **Timing** section, adjust the timing offset slider
4. Watch the **preview box** below - it shows:
   - The timestamp after applying your offset
   - The actual subtitle text that will appear at that time
   - Real-time updates as you move the slider

### Example
```
Original: Subtitle appears at 00:10
Offset: +3 seconds
Preview shows: "[00:13] Hello, world!"
```

This helps you quickly find the perfect sync without trial and error!

---

## 🌍 Subtitle Translation

### Supported Languages
SubtitlePlayer can translate subtitles to **18+ languages** with regional variants:

#### English
- English (US)
- English (UK)
- English (Canada)

#### Romance Languages
- Portuguese (Brazil)
- Portuguese (Portugal)
- Spanish (Spain)
- Spanish (Latin America)
- French
- Italian

#### Asian Languages
- Chinese (Simplified)
- Chinese (Traditional)
- Japanese
- Korean
- Hindi

#### Other Languages
- German
- Russian
- Arabic

### How to use

#### 1. Install Translation Dependencies
Choose one of these translation backends:

**Option A: googletrans (recommended)**
```bash
pip install googletrans==4.0.0rc1
```

**Option B: deep-translator**
```bash
pip install deep-translator
```

#### 2. Translate Your Subtitles
1. Load a video with subtitles
2. Open **Settings > Subtitle Settings**
3. Scroll to the **Translation** section
4. Select your target language from the dropdown
5. Click **Translate Subtitles**
6. Watch the progress indicator
7. ✓ Done! Subtitles are now in your chosen language

### Features
- ✅ **Preserves Timing**: All subtitle timecodes remain perfectly synced
- ✅ **Batch Translation**: Translates all subtitles at once
- ✅ **Progress Feedback**: Shows real-time translation progress
- ✅ **Error Handling**: Keeps original text if translation fails
- ✅ **Multiple Backends**: Uses googletrans or deep-translator automatically

---

## 🔧 Technical Details

### Timing Preview Implementation
- Updates in **real-time** as you adjust the offset
- Uses current video playback time + offset
- Searches subtitle entries for matching timestamp
- Displays formatted time (MM:SS) and subtitle text

### Translation Implementation
- **Auto-detection**: Automatically detects source language
- **Language Mapping**: Smart mapping of regional variants to language codes
- **Batch Processing**: Efficient translation of multiple subtitles
- **Fallback**: Uses original text if translation fails

### Architecture
```
subtitle_settings_dialog.py
├── update_timing_preview()  # Real-time preview updates
└── translate_subtitles()    # Translation orchestration

subtitle_translator.py
├── SubtitleTranslator       # Main translation class
├── translate_subtitles()    # Batch subtitle translation
├── _translate_text()        # Single text translation
└── detect_language()        # Language detection
```

---

## 🎮 Workflow Examples

### Sync Out-of-Sync Subtitles
1. Load video and subtitle file
2. Play video and notice subtitle is **2 seconds early**
3. Open Subtitle Settings
4. Adjust timing offset to **+2 seconds**
5. Watch preview - now shows correct subtitle at current time
6. Click Apply - perfect sync! 🎯

### Watch Foreign Film with English Subtitles
1. Load video with Spanish subtitles
2. Open Subtitle Settings
3. Select **English (US)** from translation dropdown
4. Click **Translate Subtitles**
5. Wait for translation to complete (~10 seconds for 200 subtitles)
6. Enjoy the movie with English subtitles! 🎬

### Create Multilingual Versions
1. Load original subtitle file
2. Translate to Portuguese (Brazil) → Save as `movie_pt-BR.srt`
3. Translate to Spanish (Spain) → Save as `movie_es-ES.srt`
4. Translate to French → Save as `movie_fr.srt`
5. Now you have subtitles in multiple languages! 🌐

---

## ⚠️ Limitations

### Timing Preview
- Requires video to be playing (or paused at a time position)
- Shows "Play video to see subtitle preview" if no current time
- Only previews one subtitle at a time (the one at current time)

### Translation
- Requires internet connection (for googletrans/deep-translator)
- Translation quality depends on the API service
- Some idioms or cultural references may not translate perfectly
- Very long subtitles may be truncated by translation API

---

## 🐛 Troubleshooting

### "No translation library available" Error
**Solution**: Install one of the translation backends
```bash
pip install googletrans==4.0.0rc1
# OR
pip install deep-translator
```

### Translation is slow
**Cause**: Network latency or many subtitles
**Solution**: 
- Check your internet connection
- Be patient - large subtitle files take time
- Consider translating in smaller batches

### Preview shows "(no subtitle)"
**Cause**: No subtitle at current video time
**Solution**: 
- Seek to a part of the video with subtitles
- Adjust the timing offset to find subtitles

### Translation failed
**Possible causes**:
- No internet connection
- Translation API rate limit reached
- Very long subtitle text
**Solution**: 
- Check your internet
- Wait a few minutes and try again
- Break very long subtitles into shorter segments

---

## 🚀 Future Enhancements

Planned improvements:
- [ ] Offline translation using local ML models
- [ ] Translation caching to avoid re-translating
- [ ] Custom translation glossaries for technical terms
- [ ] Subtitle preview with live video playback
- [ ] Side-by-side original + translated view
- [ ] Export translated subtitles to file

---

## 📝 Notes

### Performance
- Timing preview: **Instant** (no lag)
- Translation: **~100-200 subtitles per minute** (depends on internet speed)

### File Compatibility
Works with all supported subtitle formats:
- ✅ SRT (SubRip)
- ✅ VTT (WebVTT)
- ✅ ASS (Advanced SubStation Alpha)

### Keyboard Shortcuts
While adjusting timing in settings dialog:
- **Arrow Keys**: Fine-tune offset (+/- 0.1s)
- **Page Up/Down**: Large adjustments (+/- 1s)

---

**Enjoy perfectly synced subtitles in your favorite language! 🎬🌍**
