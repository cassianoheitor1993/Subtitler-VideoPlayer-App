# Publishing SubtitlePlayer to Ubuntu App Store

This guide covers how to build, test, and publish SubtitlePlayer to the Ubuntu App Store (Snap Store).

## 📋 Prerequisites

### 1. Snapcraft Account
- Create account at https://snapcraft.io/
- Register your email
- Set up 2FA (required for publishing)

### 2. Install Snapcraft
```bash
sudo snap install snapcraft --classic
```

### 3. Install LXD (for building snaps)
```bash
sudo snap install lxd
sudo lxd init --auto
sudo usermod -a -G lxd $USER
newgrp lxd
```

### 4. Create Application Icon
Before publishing, you **must** create an application icon:
- Size: 256x256 PNG (also create 512x512 for HiDPI)
- Location: `snap/gui/subtitleplayer.png`
- See `snap/gui/ICON_README.md` for design guidelines

---

## 🏗️ Building the Snap

### Step 1: Clean Previous Builds
```bash
cd SubtitlePlayer
snapcraft clean
```

### Step 2: Build the Snap
```bash
# Build using LXD container (recommended)
snapcraft --use-lxd

# OR build using Multipass (alternative)
snapcraft

# This will take 10-30 minutes on first build
# Output: subtitleplayer_1.1.0_amd64.snap
```

### Step 3: Verify Build
```bash
# Check snap file was created
ls -lh *.snap

# Should see: subtitleplayer_1.1.0_amd64.snap (~200-300MB)
```

---

## 🧪 Testing the Snap Locally

### Install Snap Locally
```bash
# Install in dev mode (less restrictive)
sudo snap install ./subtitleplayer_1.1.0_amd64.snap --dangerous --devmode

# OR install in strict mode (production mode)
sudo snap install ./subtitleplayer_1.1.0_amd64.snap --dangerous
```

### Test the Application
```bash
# Run from terminal
subtitleplayer

# Check if it appears in application menu
# Search for "SubtitlePlayer" in Ubuntu Activities

# Test key features:
# 1. Open a video file
# 2. Download subtitles
# 3. Customize subtitle appearance
# 4. Test AI generation (if dependencies available)
# 5. Test fullscreen (double-click)
# 6. Test context menu (right-click)
# 7. Test timeline clicking
```

### Check Snap Info
```bash
# View snap details
snap info subtitleplayer --local

# Check snap connections (permissions)
snap connections subtitleplayer

# View snap logs
snap logs subtitleplayer -f
```

### Common Issues & Fixes

#### Issue: "Permission denied" accessing files
**Fix**: Connect home interface
```bash
sudo snap connect subtitleplayer:home
```

#### Issue: No audio playback
**Fix**: Connect audio interfaces
```bash
sudo snap connect subtitleplayer:audio-playback
sudo snap connect subtitleplayer:pulseaudio
```

#### Issue: Can't access removable media (USB drives)
**Fix**: Connect removable-media interface
```bash
sudo snap connect subtitleplayer:removable-media
```

#### Issue: VLC plugins not found
**Fix**: Check VLC_PLUGIN_PATH environment variable
```bash
# Should be set automatically in snapcraft.yaml
snap run --shell subtitleplayer
echo $VLC_PLUGIN_PATH
```

### Uninstall Test Snap
```bash
sudo snap remove subtitleplayer
```

---

## 📦 Publishing to Ubuntu App Store

### Step 1: Register App Name
```bash
# Login to snapcraft
snapcraft login

# Register the name (one-time only)
snapcraft register subtitleplayer
```

### Step 2: Upload to Edge Channel (Testing)
```bash
# Upload to edge channel for testing
snapcraft upload subtitleplayer_1.1.0_amd64.snap --release=edge

# Now you can install from edge channel:
# sudo snap install subtitleplayer --edge
```

### Step 3: Test from Edge Channel
```bash
# Install from edge channel
sudo snap install subtitleplayer --edge

# Test thoroughly
# - All core features
# - Different video formats
# - Subtitle download/generation
# - Settings persistence
# - Permissions work correctly
```

### Step 4: Promote to Beta Channel
```bash
# Once edge testing is successful
snapcraft release subtitleplayer 1 beta

# Others can now test:
# sudo snap install subtitleplayer --beta
```

### Step 5: Promote to Stable (Public Release)
```bash
# After beta testing is successful
snapcraft release subtitleplayer 1 stable

# Now publicly available:
# sudo snap install subtitleplayer
```

---

## 🌟 Snap Store Listing

### Required Information

Before publishing, prepare these materials:

#### 1. Application Icon
- ✅ 256x256 PNG (required)
- ✅ 512x512 PNG (recommended)
- Location: `snap/gui/subtitleplayer.png`

#### 2. Screenshots
Create at least 3-5 screenshots showing:
- Main player window with video
- Subtitle search dialog
- AI generation interface
- Settings customization
- Context menu in action

Screenshot specifications:
- Format: PNG or JPG
- Recommended size: 1920x1080 or 1280x720
- Show actual application usage
- Use high-quality sample content

#### 3. Application Description
Already provided in `snapcraft.yaml` and `subtitleplayer.appdata.xml`

#### 4. Contact Information
- Support email: your-email@example.com
- Website: https://github.com/cassianoheitor1993/SubtitlePlayer
- Bug tracker: https://github.com/cassianoheitor1993/SubtitlePlayer/issues

### Store Listing Management

Edit your snap listing at:
https://snapcraft.io/subtitleplayer/listing

Fill in:
- ✅ Title: SubtitlePlayer
- ✅ Summary: Professional video player with subtitle download and AI generation
- ✅ Description: (from snapcraft.yaml)
- ✅ Icon: Upload subtitleplayer.png
- ✅ Screenshots: Upload 3-5 images
- ✅ Categories: Audio & Video, Utilities
- ✅ Contact: Your email
- ✅ Website: GitHub repository URL
- ✅ License: MIT

---

## 🔄 Updating the Snap

### For New Releases

1. **Update version in snapcraft.yaml**
```yaml
version: '1.2.0'
```

2. **Update appdata.xml with release notes**
```xml
<release version="1.2.0" date="2025-11-01">
  <description>
    <p>New features and improvements:</p>
    <ul>
      <li>Added feature X</li>
      <li>Fixed bug Y</li>
    </ul>
  </description>
</release>
```

3. **Rebuild and upload**
```bash
snapcraft clean
snapcraft --use-lxd
snapcraft upload subtitleplayer_1.2.0_amd64.snap --release=edge
```

4. **Test and promote**
```bash
# Test in edge
sudo snap refresh subtitleplayer --edge

# Promote to stable when ready
snapcraft release subtitleplayer <revision> stable
```

---

## 📊 Monitoring & Analytics

### View Snap Statistics
- Visit: https://snapcraft.io/subtitleplayer/metrics
- See: Install counts, active users, territories, versions

### User Feedback
- Monitor: https://snapcraft.io/subtitleplayer/reviews
- Respond to user reviews
- Address common issues

---

## 🎯 Pre-Publication Checklist

Before publishing to stable channel:

### Functionality
- [ ] All video formats play correctly
- [ ] Subtitle download works
- [ ] AI generation works (or gracefully handles missing deps)
- [ ] Settings persist across sessions
- [ ] All UI interactions work (click, double-click, right-click)
- [ ] Keyboard shortcuts work
- [ ] Fullscreen mode works

### Performance
- [ ] Video playback is smooth
- [ ] No memory leaks during extended use
- [ ] AI generation completes successfully
- [ ] App starts in <3 seconds

### Permissions
- [ ] Home directory access works
- [ ] Network access works (for subtitle download)
- [ ] Audio playback works
- [ ] All permissions are necessary (no excessive permissions)

### Documentation
- [ ] README is complete and accurate
- [ ] QUICKSTART guide works
- [ ] API_KEY_INFO explains OpenSubtitles setup
- [ ] CONTRIBUTING guide is clear
- [ ] LICENSE is present

### Store Listing
- [ ] Icon is professional and recognizable
- [ ] Screenshots show main features
- [ ] Description is clear and compelling
- [ ] Keywords are relevant
- [ ] Contact information is correct

### Legal
- [ ] All dependencies have compatible licenses
- [ ] No copyright violations
- [ ] Privacy policy (if collecting data)
- [ ] Terms of service (if applicable)

---

## 🚀 Automated Publishing (CI/CD)

### GitHub Actions Example

Create `.github/workflows/snap-publish.yml`:

```yaml
name: Publish Snap

on:
  release:
    types: [published]

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build snap
        uses: snapcore/action-build@v1
        id: build
      
      - name: Publish to edge
        uses: snapcore/action-publish@v1
        env:
          SNAPCRAFT_STORE_CREDENTIALS: ${{ secrets.SNAPCRAFT_TOKEN }}
        with:
          snap: ${{ steps.build.outputs.snap }}
          release: edge
```

Setup:
1. Generate snapcraft token: `snapcraft export-login --snaps=subtitleplayer --channels=edge,beta,stable -`
2. Add token to GitHub Secrets as `SNAPCRAFT_TOKEN`
3. Create releases on GitHub to trigger automatic publishing

---

## 📝 Support & Resources

### Official Documentation
- Snapcraft: https://snapcraft.io/docs
- Building Snaps: https://snapcraft.io/docs/creating-a-snap
- Publishing: https://snapcraft.io/docs/releasing-your-app

### Community
- Forum: https://forum.snapcraft.io/
- Discord: https://discord.gg/snapcraft
- Matrix: #snapcraft:matrix.org

### SubtitlePlayer Specific
- GitHub: https://github.com/cassianoheitor1993/SubtitlePlayer
- Issues: https://github.com/cassianoheitor1993/SubtitlePlayer/issues
- Discussions: https://github.com/cassianoheitor1993/SubtitlePlayer/discussions

---

## 🎉 Congratulations!

Once published, your app will be available to millions of Ubuntu users worldwide!

Install command for users:
```bash
sudo snap install subtitleplayer
```

Thank you for contributing to the open source community! 🚀

---

**Last Updated**: October 15, 2025
**Version**: 1.1.0
**Author**: Cassiano Heitor
