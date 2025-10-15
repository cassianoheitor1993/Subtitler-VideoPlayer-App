# Translation Performance Optimization Guide

## Current Issues

### Performance Problems
1. **Sequential Translation**: Translates one subtitle at a time (~0.5-1s each)
2. **Rate Limiting Delays**: Adds 0.5s sleep every 50 subtitles
3. **No Caching**: Repeated texts translated multiple times
4. **No Batching**: Batch API available but not used
5. **Slow Library**: googletrans 4.0.0rc1 is not optimized

### Time Analysis
For 500 subtitles:
- Current: ~250-500 seconds (4-8 minutes) 😱
  - 500 subtitles × 0.5-1s each = 250-500s
  - Plus rate limit delays: +5s
- **Expected**: 30-60 seconds (0.5-1 minute) 🎯

## Optimization Strategies

### 1. Use Batch Translation (BIGGEST WIN)

**Current**: One-by-one translation
```python
for subtitle in subtitles:
    translated = translate(subtitle.text)  # 0.5-1s each
```

**Optimized**: Batch translation
```python
texts = [s.text for s in subtitles]
translated = translate_batch(texts, batch_size=100)  # 5-10s total!
```

**Benefit**: 10-50x faster! ⚡

### 2. Implement Caching

**Problem**: Same text translated multiple times
```python
subtitle 1: "Hello"    → Translate (0.5s)
subtitle 5: "Hello"    → Translate again (0.5s) ❌
subtitle 10: "Hello"   → Translate again (0.5s) ❌
```

**Solution**: Cache translations
```python
cache = {}
if text in cache:
    return cache[text]  # Instant! ⚡
else:
    translated = translate(text)
    cache[text] = translated
    return translated
```

**Benefit**: 2-5x faster for typical subtitle files

### 3. Use Threading/Async

**Current**: Blocking, sequential
```python
for subtitle in subtitles:
    result = translate(subtitle.text)  # Wait...
```

**Optimized**: Parallel translation
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(translate, s.text) for s in subtitles]
    results = [f.result() for f in futures]
```

**Benefit**: 5-10x faster

### 4. Switch to Faster Library

**googletrans 4.0.0rc1**: Slow, buggy, unmaintained
- 0.5-1s per translation
- API issues
- Rate limiting

**Alternative: deep-translator**: Faster, maintained
- 0.1-0.3s per translation
- Better API
- More reliable

**Alternative: LibreTranslate** (self-hosted): Fastest
- 0.01-0.05s per translation
- No rate limits
- Complete control

## Implementation Plan

### Phase 1: Quick Wins (30 minutes)
1. ✅ Implement caching
2. ✅ Use batch translation when available
3. ✅ Reduce progress update frequency

**Expected improvement**: 5-10x faster

### Phase 2: Better Library (1 hour)
1. Switch to deep-translator as primary
2. Keep googletrans as fallback
3. Add configuration option

**Expected improvement**: 2-3x additional

### Phase 3: Advanced (2 hours)
1. Add threading for parallel requests
2. Implement smart chunking
3. Add translation memory

**Expected improvement**: 2-5x additional

## Code Implementation

### Optimized Translator (Phase 1)

```python
class SubtitleTranslator:
    def __init__(self):
        self.translator = None
        self.backend = None
        self.cache = {}  # Translation cache
        self._init_translator()
    
    def translate_subtitles(
        self,
        subtitles: List,
        target_language: str,
        progress_callback: Optional[Callable] = None,
        cancel_check: Optional[Callable] = None
    ) -> List:
        """Optimized translation with caching and batching"""
        
        if not subtitles:
            return []
        
        lang_code = self.LANGUAGE_CODES.get(target_language, "en")
        
        # Extract unique texts to translate
        unique_texts = {}
        for i, sub in enumerate(subtitles):
            if sub.text not in unique_texts:
                unique_texts[sub.text] = []
            unique_texts[sub.text].append(i)
        
        logger.info(f"Translating {len(unique_texts)} unique texts (from {len(subtitles)} total)")
        
        # Check cache first
        to_translate = []
        for text in unique_texts.keys():
            cache_key = f"{lang_code}:{text}"
            if cache_key not in self.cache:
                to_translate.append(text)
        
        logger.info(f"Cache hit: {len(unique_texts) - len(to_translate)}/{len(unique_texts)}")
        
        # Batch translate uncached texts
        if to_translate:
            translated_texts = self._batch_translate_optimized(
                to_translate,
                lang_code,
                progress_callback,
                cancel_check
            )
            
            # Update cache
            for original, translated in zip(to_translate, translated_texts):
                cache_key = f"{lang_code}:{original}"
                self.cache[cache_key] = translated
        
        # Build result list
        translated = []
        for i, subtitle in enumerate(subtitles):
            if cancel_check and cancel_check():
                return translated
            
            cache_key = f"{lang_code}:{subtitle.text}"
            translated_text = self.cache.get(cache_key, subtitle.text)
            
            translated_sub = type(subtitle)(
                index=subtitle.index,
                start_time=subtitle.start_time,
                end_time=subtitle.end_time,
                text=translated_text
            )
            
            if hasattr(subtitle, 'style') and subtitle.style:
                translated_sub.style = subtitle.style
            
            translated.append(translated_sub)
            
            # Progress update (every 50 subtitles)
            if progress_callback and i % 50 == 0:
                progress_callback(
                    f"Processing subtitle {i+1}/{len(subtitles)}",
                    int((i / len(subtitles)) * 100)
                )
        
        if progress_callback:
            progress_callback("Translation complete", 100)
        
        return translated
    
    def _batch_translate_optimized(
        self,
        texts: List[str],
        lang_code: str,
        progress_callback: Optional[Callable] = None,
        cancel_check: Optional[Callable] = None,
        batch_size: int = 100
    ) -> List[str]:
        """Translate texts in optimized batches"""
        
        results = []
        total = len(texts)
        
        for batch_start in range(0, total, batch_size):
            if cancel_check and cancel_check():
                # Return what we have so far + original texts for remainder
                remaining = texts[len(results):]
                return results + remaining
            
            batch_end = min(batch_start + batch_size, total)
            batch = texts[batch_start:batch_end]
            
            # Progress update
            if progress_callback:
                progress = int((batch_start / total) * 100)
                progress_callback(
                    f"Translating batch {batch_start//batch_size + 1}/{(total + batch_size - 1)//batch_size}",
                    progress
                )
            
            try:
                # Try batch translation
                if self.backend == "googletrans":
                    batch_results = self.translator.translate(batch, dest=lang_code)
                    translated_batch = [r.text if hasattr(r, 'text') else text 
                                      for r, text in zip(batch_results, batch)]
                else:
                    # Fall back to individual
                    translated_batch = [self._translate_text(t, lang_code) for t in batch]
                
                results.extend(translated_batch)
                
            except Exception as e:
                logger.warning(f"Batch translation failed: {e}, falling back to individual")
                # Fall back to individual translation
                for text in batch:
                    try:
                        translated = self._translate_text(text, lang_code)
                        results.append(translated)
                    except Exception as e2:
                        logger.error(f"Individual translation failed: {e2}")
                        results.append(text)  # Keep original
        
        return results
```

### With Threading (Phase 3)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def translate_subtitles_parallel(
    self,
    subtitles: List,
    target_language: str,
    max_workers: int = 10,
    progress_callback: Optional[Callable] = None
) -> List:
    """Ultra-fast parallel translation"""
    
    lang_code = self.LANGUAGE_CODES.get(target_language, "en")
    
    # Group subtitles by unique text
    text_groups = {}
    for i, sub in enumerate(subtitles):
        if sub.text not in text_groups:
            text_groups[sub.text] = []
        text_groups[sub.text].append(i)
    
    unique_texts = list(text_groups.keys())
    total = len(unique_texts)
    
    # Parallel translation
    translations = {}
    completed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all translation tasks
        future_to_text = {
            executor.submit(self._translate_text, text, lang_code): text
            for text in unique_texts
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_text):
            text = future_to_text[future]
            try:
                translated = future.result(timeout=10)
                translations[text] = translated
            except Exception as e:
                logger.error(f"Translation failed for '{text[:30]}...': {e}")
                translations[text] = text  # Keep original
            
            completed += 1
            if progress_callback and completed % 10 == 0:
                progress_callback(
                    f"Translated {completed}/{total}",
                    int((completed / total) * 100)
                )
    
    # Build result with translations
    translated = []
    for subtitle in subtitles:
        translated_text = translations.get(subtitle.text, subtitle.text)
        translated_sub = type(subtitle)(
            index=subtitle.index,
            start_time=subtitle.start_time,
            end_time=subtitle.end_time,
            text=translated_text
        )
        if hasattr(subtitle, 'style'):
            translated_sub.style = subtitle.style
        translated.append(translated_sub)
    
    return translated
```

## Performance Comparison

### Before Optimization
```
500 subtitles to Portuguese:
- Unique texts: 500 (no deduplication)
- Translation method: Sequential
- Cache: None
- Time: 250-500 seconds (4-8 minutes) 😱
- API calls: 500
```

### After Phase 1 (Caching + Batching)
```
500 subtitles to Portuguese:
- Unique texts: 250 (50% are duplicates)
- Translation method: Batch (100 at a time)
- Cache: In-memory
- Time: 30-60 seconds (0.5-1 minute) ✅
- API calls: 3 batches
- **Speedup: 8-10x faster**
```

### After Phase 2 (Better Library)
```
500 subtitles to Portuguese:
- Unique texts: 250
- Translation method: Batch + deep-translator
- Cache: In-memory
- Time: 15-30 seconds ⚡
- API calls: 3 batches
- **Speedup: 15-20x faster than original**
```

### After Phase 3 (Threading)
```
500 subtitles to Portuguese:
- Unique texts: 250
- Translation method: Parallel (10 threads)
- Cache: In-memory + persistent
- Time: 5-15 seconds 🚀
- API calls: 250 (parallel)
- **Speedup: 30-50x faster than original**
```

## Additional Optimizations

### 1. Persistent Cache
Save cache to disk for reuse:
```python
import json
from pathlib import Path

cache_file = Path.home() / ".subtitleplayer" / "translation_cache.json"

def load_cache(self):
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            self.cache = json.load(f)

def save_cache(self):
    cache_file.parent.mkdir(exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(self.cache, f)
```

### 2. Smart Chunking
Split long subtitles intelligently:
```python
def chunk_text(text, max_length=500):
    """Split long text at sentence boundaries"""
    if len(text) <= max_length:
        return [text]
    
    sentences = text.split('. ')
    chunks = []
    current = ""
    
    for sentence in sentences:
        if len(current) + len(sentence) <= max_length:
            current += sentence + '. '
        else:
            chunks.append(current.strip())
            current = sentence + '. '
    
    if current:
        chunks.append(current.strip())
    
    return chunks
```

### 3. Progress Estimation
Show accurate time remaining:
```python
import time

start_time = time.time()
completed = 0

def update_progress(completed, total):
    elapsed = time.time() - start_time
    rate = completed / elapsed if elapsed > 0 else 0
    remaining = (total - completed) / rate if rate > 0 else 0
    
    return f"Translating {completed}/{total} - {int(remaining)}s remaining"
```

### 4. Network Optimization
Reuse connections:
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.1)
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
```

## Implementation Priority

### Must-Have (Implement First)
1. ✅ **Caching**: 2-5x speedup, easy to implement
2. ✅ **Deduplication**: 1.5-2x speedup, very easy
3. ✅ **Batch translation**: 5-10x speedup, moderate effort

### Should-Have (Implement Next)
4. **Better library**: 2-3x additional speedup
5. **Progress updates**: Better UX
6. **Error resilience**: More robust

### Nice-to-Have (Future)
7. **Threading**: 2-5x additional speedup, complex
8. **Persistent cache**: Quality of life
9. **Time estimation**: Better UX

## Testing

### Test Script
```python
import time
from subtitle_translator import SubtitleTranslator

# Create test subtitles
subtitles = []
for i in range(500):
    subtitles.append(MockSubtitle(
        index=i,
        text=f"Test subtitle {i % 100}",  # Some duplicates
        start_time=i * 2.0,
        end_time=i * 2.0 + 1.5
    ))

# Test old method
start = time.time()
translator_old = SubtitleTranslatorOld()
result_old = translator_old.translate_subtitles(subtitles, "Portuguese (Brazil)")
time_old = time.time() - start
print(f"Old method: {time_old:.1f}s")

# Test new method
start = time.time()
translator_new = SubtitleTranslatorOptimized()
result_new = translator_new.translate_subtitles(subtitles, "Portuguese (Brazil)")
time_new = time.time() - start
print(f"New method: {time_new:.1f}s")
print(f"Speedup: {time_old/time_new:.1f}x faster")
```

## Summary

### Current Performance
- ❌ 4-8 minutes for 500 subtitles
- ❌ Sequential processing
- ❌ No caching
- ❌ Slow library

### Optimized Performance
- ✅ 30-60 seconds for 500 subtitles (Phase 1)
- ✅ 15-30 seconds with better library (Phase 2)
- ✅ 5-15 seconds with threading (Phase 3)
- ✅ **10-50x faster overall**

### Next Steps
1. Implement Phase 1 optimizations (caching + batching)
2. Test with real subtitle files
3. Measure actual speedup
4. Consider Phase 2/3 if needed

The translation SHOULD be fast (30-60s for 500 subtitles). Let's fix it! 🚀
