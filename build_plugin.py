#!/usr/bin/env python3
"""
Build script for Calibre Audiobookshelf Downloader Plugin
"""

import os
import re
import zipfile
import sys

PLUGIN_NAME = "Audiobookshelf_Downloader"
VERSION_FILE = "version.txt"
INIT_FILE = "__init__.py"
OUTPUT_FILE = None # Defined after reading version

# Files to include in the plugin (ensure version.txt is included if you want it packaged)
PLUGIN_FILES = [
    '__init__.py',
    'config.py',
    'ui.py',
    'version.txt',
    'plugin-import-name-audiobookshelf_downloader.txt',
    'README.md',
    'images/abs_icon.png'
]

def update_init_version(version_str):
    """Dynamically update the version tuple in __init__.py based on version.txt"""
    if not os.path.exists(INIT_FILE):
        print(f"ERROR: {INIT_FILE} not found!")
        return False
    
    # Convert '1.0.2' -> (1, 0, 2)
    try:
        version_tuple = tuple(int(x) for x in version_str.split('.'))
    except ValueError:
        print(f"ERROR: Invalid version format in version.txt: '{version_str}'. Use format like 1.0.2")
        return False

    with open(INIT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find 'version = (...)' in __init__.py
    pattern = r'(version\s*=\s*)\([^)]+\)'
    replacement = f'version = {version_tuple}'
    
    new_content, count = re.subn(pattern, replacement, content)
    if count == 0:
        print(f"ERROR: Could not find 'version = (...)' pattern inside {INIT_FILE}")
        return False

    with open(INIT_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  Updated {INIT_FILE} version to {version_tuple}")
    return True

def build_plugin():
    """Build the Calibre plugin ZIP file"""
    if not os.path.exists(VERSION_FILE):
        print(f"ERROR: {VERSION_FILE} not found!")
        return 1

    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        version = f.read().strip()

    output_file = f"{PLUGIN_NAME}_v{version}.zip"
    print(f"Building Calibre plugin: {PLUGIN_NAME} (v{version})")
    
    # 1. Update __init__.py automatically using version.txt
    if not update_init_version(version):
        return 1

    # 2. Remove old zip if it exists
    if os.path.exists(output_file):
        print(f"Removing old {output_file}")
        os.remove(output_file)
    
    # 3. Create the zip file
    print("Creating plugin zip file...")
    try:
        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in PLUGIN_FILES:
                if os.path.exists(file):
                    print(f"  Adding: {file}")
                    zipf.write(file, file)
                else:
                    print(f"  WARNING: {file} not found, skipping")
        
        print(f"\n✓ Plugin built successfully: {output_file}")
        print("\nTo install in Calibre:")
        print("  1. Open Calibre")
        print("  2. Go to Preferences → Plugins")
        print("  3. Click 'Load plugin from file'")
        print(f"  4. Select {output_file}")
        print("  5. Restart Calibre")
        
        return 0
    except Exception as e:
        print(f"\n✗ Failed to build plugin: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(build_plugin())