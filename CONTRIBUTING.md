# Contributing to SubtitlePlayer

First off, thank you for considering contributing to SubtitlePlayer! 🎉

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

* **Use a clear and descriptive title**
* **Describe the exact steps to reproduce the problem**
* **Provide specific examples** (screenshots, error messages, logs)
* **Describe the behavior you observed** and what you expected
* **Include your environment details** (OS, Python version, PyQt version, VLC version)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

* **Use a clear and descriptive title**
* **Provide a detailed description of the proposed feature**
* **Explain why this enhancement would be useful**
* **List any alternative solutions you've considered**

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following our coding standards
3. **Test your changes** thoroughly
4. **Update documentation** if you've changed functionality
5. **Write a clear commit message** describing your changes
6. **Submit a pull request** with a comprehensive description

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/SubtitlePlayer.git
cd SubtitlePlayer

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-qt black flake8

# Run tests
pytest tests/
```

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications:

* **Line length**: 100 characters max
* **Indentation**: 4 spaces (no tabs)
* **Imports**: Organized in groups (standard library, third-party, local)
* **Type hints**: Use when appropriate
* **Docstrings**: Google style for all public methods/classes

### Code Formatting

```bash
# Format code with black
black subtitleplayer/ tests/

# Check with flake8
flake8 subtitleplayer/ tests/
```

### Naming Conventions

* **Classes**: `PascalCase` (e.g., `VideoPlayer`, `SubtitleParser`)
* **Functions/Methods**: `snake_case` (e.g., `load_video`, `download_subtitle`)
* **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_FILE_SIZE`, `DEFAULT_FONT`)
* **Private methods**: `_leading_underscore` (e.g., `_internal_method`)

## Testing

All new features should include tests:

```python
# Example test structure
def test_subtitle_parsing():
    parser = SubtitleParser()
    subtitles = parser.parse_srt("test.srt")
    assert len(subtitles) > 0
    assert subtitles[0]['text'] is not None
```

Run tests before submitting:

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_subtitle_parser.py -v

# Run with coverage
pytest tests/ --cov=subtitleplayer --cov-report=html
```

## Git Commit Messages

* **Use present tense** ("Add feature" not "Added feature")
* **Use imperative mood** ("Move cursor to..." not "Moves cursor to...")
* **Limit first line to 72 characters**
* **Reference issues and pull requests** after the first line

Good commit messages:
```
Add click-to-seek functionality to timeline

- Implemented mouse press event handler
- Added position calculation based on click location
- Updated video player to seek on timeline click
- Fixes #123
```

## Project Structure

```
SubtitlePlayer/
├── subtitleplayer/         # Source code
│   ├── video_player.py     # Main application
│   ├── subtitle_parser.py  # Subtitle format parsing
│   ├── opensubtitles_api.py # API integration
│   └── ...
├── tests/                  # Test files
│   ├── test_video_player.py
│   ├── test_subtitle_parser.py
│   └── ...
├── docs/                   # Documentation
├── snap/                   # Snap packaging
└── README.md
```

## Feature Development Workflow

1. **Create an issue** describing the feature
2. **Discuss the approach** with maintainers
3. **Create a branch** from `main`: `feature/your-feature-name`
4. **Implement the feature** with tests
5. **Update documentation**
6. **Submit pull request** referencing the issue

## Documentation

* Update `README.md` for user-facing changes
* Update `FEATURES.md` for new features
* Add docstrings to all public methods
* Include inline comments for complex logic
* Update `IMPROVEMENTS.md` for notable enhancements

## Areas for Contribution

We especially welcome contributions in these areas:

### High Priority
- [ ] Batch subtitle generation for multiple videos
- [ ] Subtitle translation features
- [ ] Performance optimizations for large subtitle files
- [ ] Automated testing with PyQt applications
- [ ] Accessibility improvements

### Medium Priority
- [ ] Additional subtitle format support (SUB, IDX, etc.)
- [ ] Playlist management
- [ ] Keyboard shortcut customization
- [ ] Theme customization
- [ ] Thumbnail generation for timeline

### Low Priority
- [ ] Video effects and filters
- [ ] Audio equalizer
- [ ] Chapter markers
- [ ] Bookmarks
- [ ] Video trimming/editing

## Questions?

Feel free to open an issue with the `question` label or contact the maintainers.

## Recognition

Contributors will be recognized in:
* `README.md` Contributors section
* Release notes
* Project documentation

Thank you for helping make SubtitlePlayer better! 🚀
