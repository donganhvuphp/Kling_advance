#!/bin/bash

echo "🎬 Building Standalone Kling Video Generator"
echo "==========================================="

# Remove old builds
APP_NAME="KlingVideoGenerator.app"
ZIP_NAME="KlingVideoGenerator.zip"

if [ -d "$APP_NAME" ] || [ -f "$ZIP_NAME" ]; then
    echo "🗑️  Removing old builds..."
    rm -rf "$APP_NAME" "$ZIP_NAME"
fi

# Create app bundle structure
CONTENTS="$APP_NAME/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

echo "📁 Creating app bundle structure..."
mkdir -p "$MACOS"
mkdir -p "$RESOURCES"

# Copy all project files
echo "📦 Copying project files..."
cp gui_app.py "$RESOURCES/"
cp kling_engine.py "$RESOURCES/"
cp README.md "$RESOURCES/"
cp GUIDE.md "$RESOURCES/"

# Copy virtual environment
echo "🐍 Copying Python virtual environment..."
cp -R venv "$RESOURCES/"

# Copy Playwright browsers (Chromium)
echo "🌐 Copying Playwright Chromium..."
if [ -d "$HOME/Library/Caches/ms-playwright" ]; then
    mkdir -p "$RESOURCES/venv/lib/python3.13/site-packages/playwright/driver/package/.local-browsers"
    cp -R "$HOME/Library/Caches/ms-playwright/"* "$RESOURCES/venv/lib/python3.13/site-packages/playwright/driver/package/.local-browsers/"
    echo "   ✓ Chromium copied to app bundle"
else
    echo "   ⚠ Warning: Playwright browsers not found. App will use system Chrome."
fi

# Create launcher script
echo "📝 Creating launcher script..."
cat > "$MACOS/KlingVideoGenerator" << 'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
cd "$DIR"
source venv/bin/activate
python gui_app.py
EOF

chmod +x "$MACOS/KlingVideoGenerator"

# Create Info.plist
echo "📄 Creating Info.plist..."
cat > "$CONTENTS/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>KlingVideoGenerator</string>
    <key>CFBundleIdentifier</key>
    <string>com.kling.videogenerator</string>
    <key>CFBundleName</key>
    <string>Kling Video Generator</string>
    <key>CFBundleDisplayName</key>
    <string>Kling Video Generator</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Remove quarantine attribute
echo "🔓 Removing quarantine attributes..."
xattr -cr "$APP_NAME"

# Add executable permissions to all binaries
echo "🔧 Setting executable permissions..."
find "$APP_NAME" -type f -name "*.so" -exec chmod +x {} \;
find "$APP_NAME" -type f -name "*.dylib" -exec chmod +x {} \;
chmod -R +x "$RESOURCES/venv/bin/"

# Self-sign the app to avoid macOS throttling
echo "✍️ Self-signing application..."
codesign --force --deep --sign - "$APP_NAME" 2>/dev/null || echo "   ⚠ Could not sign (not critical)"

# Create ZIP file
echo "📦 Creating ZIP archive..."
zip -r -q "$ZIP_NAME" "$APP_NAME"

# Get sizes
APP_SIZE=$(du -sh "$APP_NAME" | cut -f1)
ZIP_SIZE=$(du -sh "$ZIP_NAME" | cut -f1)

echo ""
echo "=========================================="
echo "✅ Build completed successfully!"
echo "=========================================="
echo ""
echo "📦 Application: $APP_NAME ($APP_SIZE)"
echo "📦 ZIP Archive: $ZIP_NAME ($ZIP_SIZE)"
echo ""
echo "🚀 To test locally:"
echo "   open $APP_NAME"
echo ""
echo "📤 To use on another Mac:"
echo "   1. Copy $ZIP_NAME to the new Mac"
echo "   2. unzip $ZIP_NAME"
echo "   3. xattr -cr $APP_NAME"
echo "   4. open $APP_NAME"
echo ""
echo "📝 Note: This app is portable and includes all dependencies."
echo ""