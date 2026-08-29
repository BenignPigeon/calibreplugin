# Audiobookshelf Downloader for Calibre

Download ebooks from your Audiobookshelf server directly into Calibre.

## Quick Install

1. **Download**: Go to releases and download the latest version as a .zip file
2. **Install**: Calibre → Preferences → Plugins → Load plugin from file → Select the zip file you just downloaded
3. **Restart** Calibre
4. **Configure**: Preferences → Plugins → Audiobookshelf Downloader → Customize plugin
   - Enter: Server URL (e.g., `https://abs.example.com`), Username, Password
5. **Use**: Click the Audiobookshelf button in toolbar (or dropdown arrow → Download Books) → Select libraries → Start Download

## Build Yourself
To build run: `python3 build_plugin.py`

## Features

Downloads all ebooks from selected libraries  
Auto-imports to Calibre  
Supports: EPUB, PDF, MOBI, AZW, AZW3, FB2, CBZ, CBR, TXT

## Requirements

- Calibre 5.0+
- Audiobookshelf server with credentials

License: GPL v3
