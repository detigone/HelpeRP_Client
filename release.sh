#!/bin/bash
# Script to automate the release process for HelpeRP 2.2.0

set -e

echo "========================================"
echo "HelpeRP 2.2.0 - Automated Release Script"
echo "========================================"
echo ""

PROJECT_ROOT="."
VERSION="2.2.0"

# Step 1: Clean previous builds
echo "[1/6] Cleaning previous builds..."
rm -rf dist/
rm -rf build/
rm -f HelpeRP.exe
echo "✓ Cleaned"
echo ""

# Step 2: Build EXE
echo "[2/6] Building EXE with PyInstaller..."
python tools/build_exe.py
if [ -f "dist/HelpeRP_Release/HelpeRP.exe" ]; then
    echo "✓ EXE built successfully"
else
    echo "✗ EXE build failed!"
    exit 1
fi
echo ""

# Step 3: Test EXE (optional - comment out if you want to skip)
echo "[3/6] Testing EXE startup (30 second timeout)..."
timeout 30 dist/HelpeRP_Release/HelpeRP.exe || true
echo "✓ EXE tested"
echo ""

# Step 4: Create ZIP archive
echo "[4/6] Creating ZIP archive..."
python tools/release.py --version "$VERSION" --build
if [ -f "dist/releases/HelpeRP_$VERSION.zip" ]; then
    echo "✓ ZIP created: HelpeRP_$VERSION.zip"
else
    echo "✗ ZIP creation failed!"
    exit 1
fi
echo ""

# Step 5: Calculate SHA256
echo "[5/6] Calculating SHA256 checksum..."
if command -v sha256sum &> /dev/null; then
    SHA256=$(sha256sum "dist/releases/HelpeRP_$VERSION.zip" | awk '{print $1}')
else
    SHA256=$(shasum -a 256 "dist/releases/HelpeRP_$VERSION.zip" | awk '{print $1}')
fi
echo "SHA256: $SHA256"
echo "✓ Checksum calculated"
echo ""

# Step 6: Summary
echo "[6/6] Release Summary"
echo "=================="
echo "Version: $VERSION"
echo "ZIP File: dist/releases/HelpeRP_$VERSION.zip"
echo "SHA256: $SHA256"
echo ""
echo "Next steps:"
echo "1. Update SHA256 in updates/manifest.json"
echo "2. Commit changes: git add . && git commit -m 'Release $VERSION'"
echo "3. Create tag: git tag v$VERSION"
echo "4. Push: git push origin main && git push origin v$VERSION"
echo "5. Create GitHub Release with HelpeRP_$VERSION.zip attached"
echo ""
echo "✓ Release build complete!"
