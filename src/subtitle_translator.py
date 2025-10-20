#!/usr/bin/env python3
"""
Subtitle Translation Module
Handles translation of subtitle files using various translation services
"""

import srt
import time
from pathlib import Path
from typing import Optional, Callable
from datetime import timedelta
import threading  # For thread-safe cache

import logging
logger = logging.getLogger(__name__)

# Constants for file type checking
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size

import logging
import time
import gc
from typing import List, Callable, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TranslatedSubtitle:
    """Represents a translated subtitle entry"""
    start_time: float
    end_time: float
    text: str
    original_text: str


class SubtitleTranslator:
    """Handles subtitle translation using available translation services"""
    
    # Language code mappings for different APIs
    LANGUAGE_CODES = {
        "English (US)": "en",
        "English (UK)": "en",
        "English (Canada)": "en",
        "Portuguese (Brazil)": "pt",
        "Portuguese (Portugal)": "pt",
        "Spanish (Spain)": "es",
        "Spanish (Latin America)": "es",
        "Chinese (Simplified)": "zh-cn",
        "Chinese (Traditional)": "zh-tw",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Japanese": "ja",
        "Korean": "ko",
        "Russian": "ru",
        "Arabic": "ar",
        "Hindi": "hi",
        "Dutch": "nl",
        "Polish": "pl",
        "Turkish": "tr"
    }
    
    def __init__(self, resource_manager=None):
        """
        Initialize translator with available backend and hardware optimization
        
        Args:
            resource_manager: Optional ResourceManager for hardware optimization
        """
        # Import here to avoid circular dependency
        if resource_manager is None:
            from resource_manager import get_resource_manager
            resource_manager = get_resource_manager()
        
        self.resource_manager = resource_manager
        
        # Get optimized translation config
        translation_config = self.resource_manager.get_translation_config()
        
        # Rate limiting settings (optimized based on RAM)
        self.MAX_CACHE_SIZE = translation_config['cache_size']
        self.BATCH_SIZE = translation_config['batch_size']
        self.RATE_LIMIT_DELAY = translation_config['rate_limit_delay']
        
        logger.info(f"Translation optimizer: batch_size={self.BATCH_SIZE}, "
                   f"cache_size={self.MAX_CACHE_SIZE}, "
                   f"rate_limit={self.RATE_LIMIT_DELAY}s")
        
        self.translator = None
        self.backend = None
        self.cache = {}  # Translation cache for performance
        self._cache_lock = threading.Lock()  # Thread-safe cache access
        self._last_request_time = 0  # For rate limiting
        self.backend = None
        self.cache = {}  # Translation cache for performance
        
        # Try deep-translator first (most reliable)
        try:
            from deep_translator import GoogleTranslator
            self.translator = GoogleTranslator
            self.backend = "deep-translator"
            logger.info("Using deep-translator for translation (recommended)")
        except ImportError:
            pass
        
        # Try googletrans as fallback (deprecated/unreliable)
        if not self.translator:
            try:
                from googletrans import Translator
                self.translator = Translator()
                self.backend = "googletrans"
                logger.warning("Using googletrans (deprecated, may not work). Consider installing deep-translator instead.")
            except ImportError:
                pass
        
        if not self.translator:
            raise ImportError(
                "No translation library available. Install:\n"
                "  pip install deep-translator\n\n"
                "Alternative (deprecated):\n"
                "  pip install googletrans==4.0.0rc1"
            )
    
    def _manage_cache_size(self):
        """Manage cache size to prevent memory bloat (thread-safe)"""
        with self._cache_lock:
            if len(self.cache) > self.MAX_CACHE_SIZE:
                # Remove oldest 20% of entries (simple LRU approximation)
                items_to_remove = len(self.cache) // 5
                keys_to_remove = list(self.cache.keys())[:items_to_remove]
                for key in keys_to_remove:
                    del self.cache[key]
                logger.info(f"Cache trimmed: removed {items_to_remove} old entries")
                gc.collect()  # Force garbage collection after cleanup
    
    def _rate_limit(self):
        """Apply rate limiting to avoid API throttling"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()
    
    def clear_cache(self):
        """Clear translation cache to free memory (thread-safe)"""
        with self._cache_lock:
            self.cache.clear()
        gc.collect()
        logger.info("Translation cache cleared")
    
    def translate_subtitles(
        self,
        subtitles: List,
        target_language: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None
    ) -> List:
        """
        Translate a list of subtitles to the target language
        
        Args:
            subtitles: List of subtitle objects with text, start_time, end_time
            target_language: Target language name (e.g., "English (US)")
            progress_callback: Optional callback function(message, percentage)
            cancel_check: Optional callback function to check if translation should be cancelled
            
        Returns:
            List of translated subtitle objects (or partial list if cancelled)
        """
        if not subtitles:
            return []
        
        # Get language code
        lang_code = self.LANGUAGE_CODES.get(target_language, "en")
        total = len(subtitles)
        
        logger.info(f"Starting translation of {total} subtitles to {target_language} ({lang_code})")
        
        # Phase 1: Extract unique texts for translation (deduplication)
        unique_texts = {}
        for i, sub in enumerate(subtitles):
            text = sub.text.strip()
            if text not in unique_texts:
                unique_texts[text] = []
            unique_texts[text].append(i)
        
        logger.info(f"Found {len(unique_texts)} unique texts (from {total} total subtitles)")
        
        # Phase 2: Check cache and identify texts to translate
        cache_prefix = f"{lang_code}:"
        to_translate = []
        cached_count = 0
        
        with self._cache_lock:
            for text in unique_texts.keys():
                cache_key = cache_prefix + text
                if cache_key not in self.cache:
                    to_translate.append(text)
                else:
                    cached_count += 1
        
        if cached_count > 0:
            logger.info(f"Cache hit: {cached_count}/{len(unique_texts)} texts (saving {cached_count * 0.5:.1f}s)")
        
        # Phase 3: Batch translate uncached texts
        if to_translate:
            logger.info(f"Translating {len(to_translate)} new texts...")
            translations = self._batch_translate_texts(
                to_translate,
                lang_code,
                progress_callback,
                cancel_check,
                len(to_translate),
                total
            )
            
            # Update cache (thread-safe)
            with self._cache_lock:
                for original, translated in zip(to_translate, translations):
                    cache_key = cache_prefix + original
                    self.cache[cache_key] = translated
        
        # Phase 4: Build translated subtitle list
        translated = []
        
        for i, subtitle in enumerate(subtitles):
            # Check if translation should be cancelled
            if cancel_check and cancel_check():
                logger.info(f"Translation cancelled by user at subtitle {i+1}/{total}")
                if progress_callback:
                    progress_callback(f"Translation cancelled", int((i / total) * 100))
                return translated  # Return partial results
            
            # Report progress (less frequently since we're faster now)
            if progress_callback and i % 50 == 0:
                percentage = int((i / total) * 100)
                progress_callback(f"Building subtitle {i+1}/{total}", percentage)
            
            try:
                # Get translated text from cache (thread-safe)
                text = subtitle.text.strip()
                cache_key = cache_prefix + text
                with self._cache_lock:
                    translated_text = self.cache.get(cache_key, text)
                
                # Create translated subtitle object
                # Preserve original timing and structure
                translated_sub = type(subtitle)(
                    index=subtitle.index,
                    start_time=subtitle.start_time,
                    end_time=subtitle.end_time,
                    text=translated_text
                )
                
                # Preserve style if present
                if hasattr(subtitle, 'style') and subtitle.style:
                    translated_sub.style = subtitle.style
                
                translated.append(translated_sub)
                
            except Exception as e:
                logger.error(f"Error processing subtitle {i+1}: {e}")
                # Keep original subtitle on error
                translated.append(subtitle)
        
        # Final progress update
        if progress_callback:
            progress_callback(f"Translation complete", 100)
        
        logger.info(f"Successfully translated {len(translated)} subtitles")
        return translated
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text for translation (remove or handle problematic characters)
        
        Args:
            text: Original text
            
        Returns:
            Sanitized text safe for translation
        """
        if not text:
            return text
        
        # Keep the original text, just strip extra whitespace
        # Most translation APIs can handle special characters
        return text.strip()
    
    def _translate_text(self, text: str, target_lang: str) -> str:
        """
        Translate a single text string
        
        Args:
            text: Text to translate
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text
        
        # Sanitize text before translation
        clean_text = self._sanitize_text(text)
        
        try:
            if self.backend == "googletrans":
                # Using googletrans - wrap in extra error handling due to library bugs
                try:
                    result = self.translator.translate(clean_text, dest=target_lang)
                    
                    # Check if result is valid
                    if result is None or not hasattr(result, 'text'):
                        logger.debug(f"Invalid translation result for '{text[:30]}...', keeping original")
                        return text
                    
                    # Return translated text or original if empty
                    translated = result.text
                    return translated if translated else text
                    
                except AttributeError as ae:
                    # Known googletrans bug: 'Translator' object has no attribute 'raise_Exception'
                    # This happens when the API returns unexpected results
                    if 'raise_Exception' in str(ae):
                        logger.debug(f"googletrans API issue for '{text[:20]}...', keeping original")
                    else:
                        logger.debug(f"Translation attribute error: {ae}, keeping original")
                    return text
                
            elif self.backend == "deep-translator":
                # Using deep-translator
                translator = self.translator(source='auto', target=target_lang)
                translated = translator.translate(clean_text)
                return translated if translated else text
                
            else:
                logger.error("No translation backend available")
                return text
                
        except AttributeError as e:
            # Handle other NoneType or missing attributes
            logger.debug(f"Translation attribute error for '{text[:30]}...': {e}, keeping original")
            return text
        except Exception as e:
            # Catch-all for other errors
            logger.debug(f"Translation error for '{text[:30]}...': {e}, keeping original")
            return text
    
    def _batch_translate_texts(
        self,
        texts: List[str],
        lang_code: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        unique_count: int = 0,
        total_subs: int = 0,
        batch_size: int = None
    ) -> List[str]:
        """
        Optimized batch translation with progress tracking and memory management
        
        Args:
            texts: List of unique texts to translate
            lang_code: Target language code
            progress_callback: Progress callback function
            cancel_check: Cancellation check function
            unique_count: Total unique texts (for progress)
            total_subs: Total subtitle count (for context)
            batch_size: Number of texts per batch (default: self.BATCH_SIZE)
            
        Returns:
            List of translated texts (same order as input)
        """
        if batch_size is None:
            batch_size = self.BATCH_SIZE
            
        results = []
        total = len(texts)
        
        for batch_start in range(0, total, batch_size):
            # Check for cancellation
            if cancel_check and cancel_check():
                logger.info(f"Translation cancelled during batch processing")
                # Return what we have + original texts for remainder
                remaining = texts[len(results):]
                return results + remaining
            
            batch_end = min(batch_start + batch_size, total)
            batch = texts[batch_start:batch_end]
            batch_num = batch_start // batch_size + 1
            total_batches = (total + batch_size - 1) // batch_size
            
            # Progress update
            if progress_callback:
                progress = int((batch_start / unique_count) * 90)  # Reserve 10% for building
                progress_callback(
                    f"Translating batch {batch_num}/{total_batches} ({len(batch)} texts)",
                    progress
                )
            
            logger.debug(f"Translating batch {batch_num}/{total_batches}: {len(batch)} texts")
            
            # Apply rate limiting before each batch
            self._rate_limit()
            
            try:
                # Try batch translation first
                if self.backend == "googletrans" and len(batch) > 1:
                    try:
                        batch_results = self.translator.translate(batch, dest=lang_code)
                        
                        # Extract translated texts, handle errors gracefully
                        translated_batch = []
                        for i, (result, original) in enumerate(zip(batch_results, batch)):
                            if result and hasattr(result, 'text') and result.text:
                                translated_batch.append(result.text)
                            else:
                                logger.debug(f"Batch item {i} failed, keeping original")
                                translated_batch.append(original)
                        
                        results.extend(translated_batch)
                        logger.debug(f"Batch {batch_num} completed successfully")
                        
                        # Manage cache size periodically
                        if batch_num % 10 == 0:
                            self._manage_cache_size()
                        
                        continue  # Success, move to next batch
                        
                    except Exception as e:
                        logger.warning(f"Batch translation failed for batch {batch_num}: {e}")
                        # Fall through to individual translation
                
                # Fall back to individual translation
                logger.debug(f"Using individual translation for batch {batch_num}")
                for text in batch:
                    try:
                        self._rate_limit()  # Rate limit each individual request
                        translated = self._translate_text(text, lang_code)
                        results.append(translated)
                    except Exception as e:
                        logger.error(f"Individual translation failed: {e}")
                        results.append(text)  # Keep original
                
                # Small delay between batches to avoid rate limiting
                if batch_end < total:
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Batch {batch_num} failed completely: {e}")
                # Keep all original texts for this batch
                results.extend(batch)
        
        logger.info(f"Batch translation completed: {len(results)}/{total} texts")
        return results
    
    def batch_translate(
        self,
        texts: List[str],
        target_lang: str
    ) -> List[str]:
        """
        Translate multiple texts at once (more efficient for some APIs)
        
        Args:
            texts: List of texts to translate
            target_lang: Target language code
            
        Returns:
            List of translated texts
        """
        if self.backend == "googletrans":
            try:
                # googletrans supports batch translation
                results = self.translator.translate(texts, dest=target_lang)
                return [r.text for r in results]
            except Exception as e:
                logger.error(f"Batch translation failed: {e}")
                # Fall back to individual translation
                return [self._translate_text(t, target_lang) for t in texts]
        else:
            # deep-translator doesn't support batch, translate individually
            return [self._translate_text(t, target_lang) for t in texts]
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of a text
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code (e.g., 'en', 'pt', 'es')
        """
        try:
            if self.backend == "googletrans":
                result = self.translator.detect(text)
                return result.lang
            elif self.backend == "deep-translator":
                from deep_translator import single_detection
                return single_detection(text, api_key=None)
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "unknown"
