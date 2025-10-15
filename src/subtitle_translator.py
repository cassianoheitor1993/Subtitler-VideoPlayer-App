#!/usr/bin/env python3
"""
Subtitle Translation Module
Handles subtitle translation to multiple languages using translation APIs
"""

import logging
import time
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
        "Hindi": "hi"
    }
    
    def __init__(self):
        """Initialize translator with available backend"""
        self.translator = None
        self.backend = None
        
        # Try googletrans first
        try:
            from googletrans import Translator
            self.translator = Translator()
            self.backend = "googletrans"
            logger.info("Using googletrans for translation")
        except ImportError:
            pass
        
        # Try deep-translator as fallback
        if not self.translator:
            try:
                from deep_translator import GoogleTranslator
                self.translator = GoogleTranslator
                self.backend = "deep-translator"
                logger.info("Using deep-translator for translation")
            except ImportError:
                pass
        
        if not self.translator:
            raise ImportError(
                "No translation library available. Install one of:\n"
                "  pip install googletrans==4.0.0rc1\n"
                "  pip install deep-translator"
            )
    
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
        
        translated = []
        total = len(subtitles)
        
        logger.info(f"Starting translation of {total} subtitles to {target_language} ({lang_code})")
        
        for i, subtitle in enumerate(subtitles):
            # Check if translation should be cancelled
            if cancel_check and cancel_check():
                logger.info(f"Translation cancelled by user at subtitle {i+1}/{total}")
                if progress_callback:
                    progress_callback(f"Translation cancelled", int((i / total) * 100))
                return translated  # Return partial results
            
            try:
                # Report progress
                if progress_callback and i % 10 == 0:
                    percentage = int((i / total) * 100)
                    progress_callback(f"Translating subtitle {i+1}/{total}", percentage)
                
                # Translate the text
                translated_text = self._translate_text(subtitle.text, lang_code)
                
                # Check if translation actually happened (not just returned original)
                if translated_text == subtitle.text and len(subtitle.text) > 1:
                    logger.debug(f"Subtitle {i+1} unchanged, possibly untranslatable or already in target language")
                
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
                
                # Small delay to avoid rate limiting (every 50 subtitles)
                if (i + 1) % 50 == 0 and i < total - 1:
                    time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error translating subtitle {i+1}: {e}")
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
