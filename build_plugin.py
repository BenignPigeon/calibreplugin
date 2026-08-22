#!/usr/bin/env python3
"""
Build script for Calibre Audiobookshelf Downloader Plugin
"""

import os
import zipfile
import sys

PLUGIN_NAME = "Audiobookshelf_Downloader"
VERSION = "1.0.2"
OUTPUT_FILE = f"{PLUGIN_NAME}_v{VERSION}.zip"

# Files to include in the plugin
PLUGIN_FILES = [
    '__init__.py',
    'config.py',
    'ui.py',
    'plugin-import-name-audiobookshelf_downloader.txt',
    'README.md',
    'images/abs_icon.png'
]

def build_plugin():
    """Build the Calibre plugin ZIP file"""
    print(f"Building Calibre plugin: {PLUGIN_NAME}")
    
    # Remove old zip if it exists
    if os.path.exists(OUTPUT_FILE):
        print(f"Removing old {OUTPUT_FILE}")
        os.remove(OUTPUT_FILE)
    
    # Create the zip file
    print("Creating plugin zip file...")
    try:
        with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in PLUGIN_FILES:
                if os.path.exists(file):
                    print(f"  Adding: {file}")
                    # Preserve directory structure
                    zipf.write(file, file)
                else:
                    print(f"  WARNING: {file} not found, skipping")
        
        print(f"\n✓ Plugin built successfully: {OUTPUT_FILE}")
        print("\nTo install in Calibre:")
        print("  1. Open Calibre")
        print("  2. Go to Preferences → Plugins")
        print("  3. Click 'Load plugin from file'")
        print(f"  4. Select {OUTPUT_FILE}")
        print("  5. Restart Calibre")
        print("  6. Configure the plugin in Preferences → Plugins → Audiobookshelf Downloader")
        
        return 0
    except Exception as e:
        print(f"\n✗ Failed to build plugin: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(build_plugin())
