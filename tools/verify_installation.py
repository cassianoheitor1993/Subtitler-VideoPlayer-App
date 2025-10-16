#!/usr/bin/env python3
"""
SubtitlePlayer Installation Verification Script
Run this to check if all dependencies are properly installed
"""

import sys
import os

def check_python_version():
    """Check Python version"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor}.{version.micro} (Need 3.8+)")
        return False

def check_module(module_name, import_name=None):
    """Check if a Python module is installed"""
    if import_name is None:
        import_name = module_name
    
    try:
        __import__(import_name)
        print(f"  ✓ {module_name}")
        return True
    except ImportError:
        print(f"  ✗ {module_name} (Not installed)")
        return False

def check_vlc():
    """Check VLC installation"""
    print("\nChecking VLC...")
    
    # Check if VLC command exists
    vlc_installed = os.system("which vlc > /dev/null 2>&1") == 0
    if vlc_installed:
        print("  ✓ VLC installed")
    else:
        print("  ✗ VLC not installed")
        return False
    
    # Check python-vlc binding
    try:
        import vlc
        print("  ✓ python-vlc binding")
        return True
    except ImportError:
        print("  ✗ python-vlc binding (Not installed)")
        return False

def check_project_structure():
    """Check if project files exist"""
    print("\nChecking project structure...")
    
    files_to_check = [
        "main.py",
        "requirements.txt",
        "run.sh",
        "install.sh",
        "README.md",
        "src/video_player.py",
        "src/opensubtitles_api.py",
        "src/subtitle_parser.py",
        "src/subtitle_search_dialog.py",
        "src/subtitle_settings_dialog.py",
        "src/config_manager.py"
    ]
    
    all_exist = True
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} (Missing)")
            all_exist = False
    
    return all_exist

def main():
    """Main verification function"""
    print("=" * 60)
    print("  SubtitlePlayer Installation Verification")
    print("=" * 60)
    print()
    
    results = []
    
    # Check Python version
    results.append(check_python_version())
    
    # Check Python modules
    print("\nChecking Python dependencies...")
    results.append(check_module("PyQt6"))
    results.append(check_module("requests"))
    results.append(check_module("chardet"))
    results.append(check_module("pysrt"))
    
    # Check VLC
    results.append(check_vlc())
    
    # Check project structure
    results.append(check_project_structure())
    
    # Summary
    print("\n" + "=" * 60)
    if all(results):
        print("  ✓✓✓ All checks passed! SubtitlePlayer is ready to run.")
        print("=" * 60)
        print("\nTo run the application:")
        print("  ./run.sh")
        print("\nOr manually:")
        print("  source venv/bin/activate")
        print("  python3 main.py")
        return 0
    else:
        print("  ✗✗✗ Some checks failed. Please fix the issues above.")
        print("=" * 60)
        print("\nTo install missing dependencies:")
        print("  ./install.sh")
        print("\nOr manually:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
