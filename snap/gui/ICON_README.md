# Icon Placeholder
# 
# This is a placeholder for the SubtitlePlayer application icon.
# 
# To create a proper icon:
# 1. Create a 256x256 PNG image with your application icon
# 2. Name it subtitleplayer.png
# 3. Place it in this directory (snap/gui/)
# 
# Icon Requirements for Ubuntu App Store:
# - Format: PNG
# - Size: 256x256 pixels (recommended), also provide 512x512 for HiDPI
# - Transparent background (optional but recommended)
# - Follow Ubuntu icon design guidelines
# - Should be recognizable at small sizes (48x48, 32x32)
# 
# Suggested Icon Design:
# - Play button symbol (triangle) combined with subtitle lines (===)
# - Color scheme: Professional blues/purples or media player theme
# - Clean, modern, minimalist design
# - Avoid text in the icon (except logo if applicable)
# 
# You can create the icon using:
# - GIMP (free, open source)
# - Inkscape (vector graphics, export to PNG)
# - Figma (online design tool)
# - Icon generators online
# 
# Example command to create a simple placeholder icon:
# convert -size 256x256 xc:transparent -fill '#4285F4' -draw "polygon 80,60 80,196 200,128" -fill '#34A853' -draw "rectangle 60,210 240,220" -draw "rectangle 60,230 220,240" -draw "rectangle 60,250 200,260" subtitleplayer.png

# For now, you can use this SVG code and convert it to PNG:
# (Paste this into an online SVG to PNG converter)
#
# <svg width="256" height="256" xmlns="http://www.w3.org/2000/svg">
#   <rect width="256" height="256" fill="#4285F4" rx="40"/>
#   <polygon points="90,70 90,186 200,128" fill="white"/>
#   <rect x="60" y="200" width="180" height="8" fill="white" rx="2"/>
#   <rect x="60" y="215" width="160" height="8" fill="white" rx="2"/>
#   <rect x="60" y="230" width="140" height="8" fill="white" rx="2"/>
# </svg>
