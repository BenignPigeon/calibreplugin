# Audiobookshelf Downloader for Calibre

Download ebooks from your Audiobookshelf server directly into Calibre.

## Quick Install

1. **Build**: `python3 build_plugin.py`
2. **Install**: Calibre → Preferences → Plugins → Load plugin from file → Select `Audiobookshelf_Downloader_v1.0.0.zip`
3. **Restart** Calibre
4. **Configure**: Preferences → Plugins → Audiobookshelf Downloader → Customize plugin
   - Enter: Server URL (e.g., `https://abs.example.com`), Username, Password
5. **Use**: Click the Audiobookshelf button in toolbar (or dropdown arrow → Download Books) → Select libraries → Start Download

## Features

✅ Downloads all ebooks from selected libraries  
✅ Auto-imports to Calibre  
✅ Progress tracking  
✅ Supports: EPUB, PDF, MOBI, AZW, AZW3, FB2, CBZ, CBR, TXT

## Troubleshooting

**Button doesn't appear?** → Restart Calibre  
**"Configuration Required"?** → Configure plugin first (step 4)  
**Authentication fails?** → Check URL includes `http://` or `https://`, verify credentials  
**No libraries?** → Verify libraries exist in Audiobookshelf and user has access

## Requirements

- Calibre 5.0+
- Audiobookshelf server with credentials

## Files

- `Audiobookshelf_Downloader_v1.0.0.zip` - Install this file
- `build_plugin.py` - Build script
- Source: `__init__.py`, `config.py`, `ui.py`

License: GPL v3
