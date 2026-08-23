# AGENTS.md - AI Coding Agent Instructions

## Project Overview
Calibre plugin that downloads ebooks from an Audiobookshelf server and imports them directly into Calibre's library. Built with Python 3, PyQt5, and Calibre's plugin API.

## Tech Stack
- **Language**: Python 3 (compatible with Python 2 via `__future__` imports)
- **GUI Framework**: PyQt5 (Calibre's Qt bindings)
- **Plugin Type**: Calibre InterfaceAction plugin
- **HTTP**: `urllib.request` (no external dependencies)
- **Config Storage**: Calibre's `JSONConfig`

## Setup & Build

### Install (No dependencies needed - uses Calibre's bundled libraries)
```bash
# No pip install required - all dependencies come with Calibre
```

### Build Plugin
```bash
python3 build_plugin.py
# Output: Audiobookshelf_Downloader_v{version}.zip
```

### Install in Calibre
1. Calibre → Preferences → Plugins → Load plugin from file
2. Select `Audiobookshelf_Downloader_v{version}.zip`
3. Restart Calibre

### Version Management
- Version is stored in `version.txt` (format: `1.0.3`)
- Build script auto-updates `__init__.py` version tuple from `version.txt`
- To bump version: edit `version.txt`, then run `build_plugin.py`

## Architecture & Key Files

```
.
├── __init__.py              # Plugin entry point (InterfaceActionBase)
├── config.py                # Configuration dialog (QWidget)
├── ui.py                    # Main UI logic (InterfaceAction + dialogs)
├── version.txt              # Single source of truth for version
├── build_plugin.py          # Build script (creates ZIP)
├── plugin-import-name-*.txt # Calibre plugin identifier
├── images/abs_icon.png      # Plugin toolbar icon
└── README.md                # User documentation
```

### Core Components (821 lines total)

**`__init__.py` (61 lines)**
- `AudiobookshelfDownloaderPlugin(InterfaceActionBase)` - Plugin registration
- Defines metadata: name, version, author, description
- Links to `ui.AudiobookshelfDownloaderAction` as `actual_plugin`
- Provides `config_widget()` and `save_settings()` methods
- **CRITICAL**: Enables `faulthandler` to debug segfaults

**`config.py` (105 lines)**
- `ConfigWidget(QWidget)` - Settings UI
- `prefs = JSONConfig('plugins/audiobookshelf_downloader')` - Config storage
- Settings: `server_url`, `username`, `password`, `auto_import`, `skip_duplicates`
- All defaults defined in `prefs.defaults` dict

**`ui.py` (655 lines)** - Main logic
- `AudiobookshelfDownloaderAction(InterfaceAction)` - Toolbar button
- `LibrarySelectDialog(QDialog)` - Library selection UI
- `DownloadDialog(QDialog)` - Progress window with download thread
- HTTP API calls to Audiobookshelf (login, libraries, items, download)
- Duplicate detection via `is_duplicate()` (searches Calibre DB by title/author)
- Import logic adds books to Calibre database

## Key Behaviors & Constraints

### Duplicate Detection (Default: Enabled)
- Searches Calibre DB for matching title (exact match)
- If authors exist, compares author names (case-insensitive, any match)
- Skips import if duplicate found
- Configurable via `prefs['skip_duplicates']`

### Authentication & Cloudflare
**MUST** include User-Agent header on all requests to bypass Cloudflare bot protection:
```python
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
```

### Threading Model
- Main UI runs in Qt main thread
- Downloads run in background thread (`threading.Thread`)
- Use `QApplication.processEvents()` for UI responsiveness
- Thread is daemon for clean shutdown

## API Endpoints (Audiobookshelf)

```python
POST   /login                                    # Auth → returns token
GET    /api/libraries                            # List libraries
GET    /api/libraries/{id}/items                 # Items in library
GET    /api/items/{id}                           # Item details
GET    /api/items/{id}/file/{ino}/download      # Download file
```

## Code Style & Guidelines

### Import Order
1. `__future__` imports first
2. License/copyright docstrings
3. Standard library (json, urllib, os, threading)
4. PyQt5 imports
5. Calibre imports
6. Local imports

### Naming Conventions
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_CASE`
- Private methods: `_leading_underscore`

### Calibre Plugin Patterns
```python
# Plugin entry point
class MyPlugin(InterfaceActionBase):
    name = 'Plugin Name'
    actual_plugin = 'calibre_plugins.module.ui:ActionClass'

# Action class
class MyAction(InterfaceAction):
    action_spec = ('Plugin Name', None, 'Tooltip', None)
    popup_type = QToolButton.MenuButtonPopup  # For dropdown arrow
```

### Error Handling
- Wrap all background thread logic in try/except
- Log errors to dialog's QTextEdit log widget
- Always enable close button in `finally` block
- Use `import traceback; traceback.format_exc()` for detailed errors

### String Formats
- Use f-strings for formatting: `f"Text {var}"`
- For Calibre DB queries: Use format strings with proper escaping

## Common Pitfalls to Avoid

1. **❌ GUI updates from background thread** → Segfault
2. **❌ Missing User-Agent header** → Cloudflare 403 errors
3. **❌ Not handling dialog close properly** → Calibre crashes on exit
4. **❌ Hardcoded version in __init__.py** → Use `version.txt` + build script
5. **❌ Forgetting `faulthandler.enable()`** → Harder to debug crashes

## Testing

### Manual Testing Steps
```bash
# 1. Build plugin
python3 build_plugin.py

# 2. Install in Calibre (see Install in Calibre section)

# 3. Test authentication
# - Configure server, username, password
# - Click plugin button
# - Should authenticate successfully

# 4. Test download
# - Select libraries
# - Watch progress dialog
# - Verify books imported (press F5 in Calibre)

# 5. Test duplicate detection
# - Download same library again
# - Should show "⊘ Skipped (already in library)" messages
```

### No Automated Tests
This project has no unit tests. All testing is manual in Calibre.

## Debugging

### Enable Verbose Logging
```python
# Already enabled in __init__.py
import faulthandler
faulthandler.enable()  # Prints segfault tracebacks to stderr
```

### Check Calibre Logs
```
Calibre → Preferences → Miscellaneous → Open calibre configuration directory
# Look for calibre-debug.log
```

### Common Debug Points
- Authentication failures: Check server_url format (include http/https)
- Import failures: Check file permissions on Calibre library
- Segfaults: Check if GUI refresh was called from background thread

## Version History

- **v1.0.3** (current) - Segfault fix (removed GUI refresh), duplicate detection
- **v1.0.2** - Improved error handling
- **v1.0.1** - Cloudflare authentication fix
- **v1.0.0** - Initial release

## Quick Reference: Key Methods

```python
# ui.py - Main download logic
def download_process(self):           # Background thread entry point
def authenticate(self):                # Get auth token
def process_item(self, item_id, ...): # Download single item
def import_to_calibre(self):          # Add to Calibre DB
def is_duplicate(self, db, mi):       # Check if book exists

# config.py - Settings
def save_settings(self):              # Save user config
```

## Plugin Lifecycle

```
1. User clicks button → genesis() called once
2. show_dialog() / download_books() called on click
3. Authenticate with server
4. Show library selection dialog
5. User selects libraries → show download dialog
6. Background thread downloads files
7. Import to Calibre database (in same thread)
8. Show "Press F5 to see books" message
9. Close dialog
```

## License
GPL v3
