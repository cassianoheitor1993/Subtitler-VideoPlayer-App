#!/bin/bash

# GitHub Push Helper Script for SubtitlePlayer
# This script helps you push your code to GitHub

echo "🚀 SubtitlePlayer - GitHub Push Helper"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "src/video_player.py" ]; then
    echo "❌ Error: Not in SubtitlePlayer directory"
    echo "Please run this script from the SubtitlePlayer root directory"
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Error: Git repository not initialized"
    echo "Run: git init"
    exit 1
fi

echo "📝 Please enter your GitHub username:"
read -r GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ Error: GitHub username cannot be empty"
    exit 1
fi

echo ""
echo "🔍 Checking current git remote..."
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null)

if [ -n "$CURRENT_REMOTE" ]; then
    echo "⚠️  Remote 'origin' already exists: $CURRENT_REMOTE"
    echo "Do you want to update it? (y/n)"
    read -r UPDATE_REMOTE
    
    if [ "$UPDATE_REMOTE" = "y" ] || [ "$UPDATE_REMOTE" = "Y" ]; then
        git remote remove origin
        echo "✅ Removed old remote"
    else
        echo "❌ Cancelled. Remove remote manually with: git remote remove origin"
        exit 1
    fi
fi

echo ""
echo "🔗 Adding GitHub remote..."
REPO_URL="https://github.com/$GITHUB_USERNAME/SubtitlePlayer.git"
git remote add origin "$REPO_URL"

if [ $? -eq 0 ]; then
    echo "✅ Remote added successfully: $REPO_URL"
else
    echo "❌ Error adding remote"
    exit 1
fi

echo ""
echo "📊 Current git status:"
git status --short

echo ""
echo "📤 Ready to push to GitHub!"
echo ""
echo "⚠️  IMPORTANT: Before pushing, make sure you've created the repository on GitHub:"
echo "   1. Go to: https://github.com/new"
echo "   2. Repository name: SubtitlePlayer"
echo "   3. Make it Public (for open source)"
echo "   4. Do NOT initialize with README, .gitignore, or license"
echo "   5. Click 'Create repository'"
echo ""
echo "Have you created the repository on GitHub? (y/n)"
read -r REPO_CREATED

if [ "$REPO_CREATED" != "y" ] && [ "$REPO_CREATED" != "Y" ]; then
    echo ""
    echo "📋 Please create the repository on GitHub first, then run:"
    echo "   git push -u origin main"
    exit 0
fi

echo ""
echo "🚀 Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Your code is now on GitHub!"
    echo ""
    echo "🔗 View your repository at:"
    echo "   https://github.com/$GITHUB_USERNAME/SubtitlePlayer"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Add repository topics (video-player, python, pyqt6, subtitles, ai)"
    echo "   2. Add repository description in Settings"
    echo "   3. Enable Issues and Discussions in Settings"
    echo "   4. Create your first release (v1.1.0)"
    echo ""
    echo "📖 See GITHUB_SETUP.md for detailed instructions"
else
    echo ""
    echo "❌ Push failed. Possible reasons:"
    echo "   - Repository doesn't exist on GitHub"
    echo "   - Authentication failed (may need to use SSH or Personal Access Token)"
    echo "   - Network issues"
    echo ""
    echo "💡 Try using SSH instead:"
    echo "   git remote remove origin"
    echo "   git remote add origin git@github.com:$GITHUB_USERNAME/SubtitlePlayer.git"
    echo "   git push -u origin main"
fi
