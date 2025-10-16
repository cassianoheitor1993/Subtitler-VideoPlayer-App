#!/bin/bash
# Install optional translation dependencies for SubtitlePlayer

echo "================================================="
echo "SubtitlePlayer - Translation Dependencies Setup"
echo "================================================="
echo ""
echo "This script will install optional translation libraries"
echo "that enable the subtitle translation feature."
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  WARNING: No virtual environment detected!"
    echo ""
    echo "It's recommended to activate your virtual environment first:"
    echo "  source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

echo "Choose a translation backend:"
echo ""
echo "1) googletrans (recommended)"
echo "   - Easy to use"
echo "   - Good translation quality"
echo "   - Free tier available"
echo ""
echo "2) deep-translator"
echo "   - Multiple translation engines"
echo "   - More configuration options"
echo "   - Good for advanced users"
echo ""
echo "3) Both (recommended for best compatibility)"
echo ""
read -p "Enter choice (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "📦 Installing googletrans..."
        pip install googletrans==4.0.0rc1
        ;;
    2)
        echo ""
        echo "📦 Installing deep-translator..."
        pip install deep-translator
        ;;
    3)
        echo ""
        echo "📦 Installing both translation libraries..."
        pip install googletrans==4.0.0rc1 deep-translator
        ;;
    *)
        echo "❌ Invalid choice. Installation cancelled."
        exit 1
        ;;
esac

# Check installation
echo ""
echo "🔍 Verifying installation..."
python3 -c "
try:
    import googletrans
    print('✅ googletrans: Installed')
except ImportError:
    print('⚠️  googletrans: Not installed')

try:
    import deep_translator
    print('✅ deep-translator: Installed')
except ImportError:
    print('⚠️  deep-translator: Not installed')
"

echo ""
echo "================================================="
echo "✓ Installation complete!"
echo "================================================="
echo ""
echo "You can now use subtitle translation in SubtitlePlayer:"
echo "  1. Open a video with subtitles"
echo "  2. Go to Settings > Subtitle Settings"
echo "  3. Scroll to Translation section"
echo "  4. Select target language and click Translate"
echo ""
echo "Supported languages:"
echo "  - English (US/UK/Canada)"
echo "  - Portuguese (Brazil/Portugal)"
echo "  - Spanish (Spain/Latin America)"
echo "  - Chinese (Simplified/Traditional)"
echo "  - French, German, Italian"
echo "  - Japanese, Korean, Russian"
echo "  - Arabic, Hindi, and more!"
echo ""
echo "For more details, see: TIMING_TRANSLATION_FEATURES.md"
echo ""
