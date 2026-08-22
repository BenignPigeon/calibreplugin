#!/bin/bash

# Build script for Calibre Audiobookshelf Downloader Plugin

PLUGIN_NAME="Audiobookshelf_Downloader"
VERSION="1.0.2"
OUTPUT_FILE="${PLUGIN_NAME}_v${VERSION}.zip"

echo "Building Calibre plugin: ${PLUGIN_NAME}"

# Remove old zip if it exists
if [ -f "${OUTPUT_FILE}" ]; then
    echo "Removing old ${OUTPUT_FILE}"
    rm "${OUTPUT_FILE}"
fi

# Create the zip file with required plugin files
echo "Creating plugin zip file..."
zip -r "${OUTPUT_FILE}" \
    __init__.py \
    config.py \
    ui.py \
    plugin-import-name-audiobookshelf_downloader.txt \
    README.md \
    -x "*.pyc" -x "__pycache__/*" -x ".*" -x "what-i-have/*"

if [ $? -eq 0 ]; then
    echo "✓ Plugin built successfully: ${OUTPUT_FILE}"
    echo ""
    echo "To install in Calibre:"
    echo "  1. Open Calibre"
    echo "  2. Go to Preferences → Plugins"
    echo "  3. Click 'Load plugin from file'"
    echo "  4. Select ${OUTPUT_FILE}"
    echo "  5. Restart Calibre"
    echo "  6. Configure the plugin in Preferences → Plugins → Audiobookshelf Downloader"
else
    echo "✗ Failed to build plugin"
    exit 1
fi
