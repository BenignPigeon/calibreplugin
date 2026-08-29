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
- Version is stored in `version.txt` (format: `1.0.4`)
- Build script auto-updates `__init__.py` version tuple from `version.txt`
- To bump version: edit `version.txt`, then run `build_plugin.py`

## Architecture & Key Files

```
.
├── __init__.py              # Plugin entry point (InterfaceActionBase) — zip root
├── main.py                  # Toolbar, dropdown menu, dialog routing
├── core/
│   ├── __init__.py
│   ├── config.py            # Preferences / Customise Plugin dialog
│   ├── api.py               # Audiobookshelf HTTP client
│   ├── calibre_import.py    # Duplicate check + add_books
│   ├── select_dialogs.py    # Shared checkbox-list UI + library/book pickers
│   └── downloader.py        # Progress dialog + background download
├── version.txt              # Single source of truth for version
├── build_plugin.py          # Build script (creates ZIP)
├── plugin-import-name-*.txt # Calibre package name (required)
├── images/abs_icon.png      # Plugin toolbar icon
├── README.md                # User documentation
├── AGENTS.md                # Agent instructions
└── info.md                  # Brief map of coding files
```

Calibre expects `__init__.py` at the **zip root**. The package name is `calibre_plugins.audiobookshelf_downloader` from `plugin-import-name-audiobookshelf_downloader.txt`, not from a wrapping folder. Python modules cannot use hyphens (`select_dialogs.py`, not `select-dialogs.py`).

### Core Components

**`__init__.py`**
- `AudiobookshelfDownloaderPlugin(InterfaceActionBase)` - Plugin registration
- Defines metadata: name, version, author, description
- Links to `main.AudiobookshelfDownloaderAction` as `actual_plugin`
- Provides `config_widget()` and `save_settings()` methods
- **CRITICAL**: Enables `faulthandler` to debug segfaults

**`main.py`**
- `AudiobookshelfDownloaderAction(InterfaceAction)` - Toolbar button and menu
- Orchestrates: config check → login → library select → fetch items → book select → download dialog

**`core/config.py`**
- `ConfigWidget(QWidget)` - Settings UI
- `prefs = JSONConfig('plugins/audiobookshelf_downloader')` - Config storage
- Settings: `server_url`, `username`, `password`, `auto_import`, `skip_duplicates`, `selected_library_ids`

**`core/api.py`**
- `AbsClient` - login, libraries, paginated items, item details, file download
- Shared User-Agent + Bearer headers
- `normalize_item()` for the book picker

**`core/select_dialogs.py`**
- `CheckableListDialog` - searchable checkbox list; Select All/None and accept() use **visible rows only**
- Default (Enter) button is Next / Download Selected, not Select All
- `LibrarySelectDialog` - restores `prefs['selected_library_ids']` (checked vs unchecked); first run or no matching IDs → all checked
- `ItemSelectDialog` - books start checked; display text is title/author/library

**`core/downloader.py`**
- `DownloadDialog` - progress UI and daemon download thread
- Receives selected items only (does not re-scan libraries)

**`core/calibre_import.py`**
- `is_duplicate()` and `import_files()`

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
- Library/item lists are fetched on the main thread (wait cursor)
- Downloads run in background thread (`threading.Thread`)
- Use `QApplication.processEvents()` for UI responsiveness
- Thread is daemon for clean shutdown
- Library view refresh must use a Qt signal (`refresh_gui_signal`) so it runs on the GUI thread

## API Endpoints (Audiobookshelf)

```python
POST   /login                                    # Auth → returns token
GET    /api/libraries                            # List libraries
GET    /api/libraries/{id}/items                 # Items in library (paginated)
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
6. Local imports (`calibre_plugins.audiobookshelf_downloader...` or relative `.api`)

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
    actual_plugin = 'calibre_plugins.module.main:ActionClass'

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

1. **GUI updates from background thread** → Segfault
2. **Missing User-Agent header** → Cloudflare 403 errors
3. **Not handling dialog close properly** → Calibre crashes on exit
4. **Hardcoded version in __init__.py** → Use `version.txt` + build script
5. **Forgetting `faulthandler.enable()`** → Harder to debug crashes
6. **Extra folder wrapping the zip** → Calibre cannot find `__init__.py`
7. **Hyphenated module names** → ImportError

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
# - Select libraries (previous picks restored; search/filter works; Enter = Next)
# - Select books (search/filter + Download Selected only include visible checks)
# - Watch progress dialog
# - Verify books imported (press F5 in Calibre)

# 5. Test duplicate detection
# - Download the same books again
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

- **v1.0.4** (current) - Library/book pickers, remembered libraries, visible-only accept
- **v1.0.3** - Segfault fix (GUI refresh via signal), duplicate detection
- **v1.0.2** - Improved error handling
- **v1.0.1** - Cloudflare authentication fix
- **v1.0.0** - Initial release

## Quick Reference: Key Methods

```python
# main.py
def download_books(self):             # Orchestrates picker + download

# core/api.py
def login(self, username, password)
def get_libraries(self)
def get_library_items(self, library_id)
def get_item(self, item_id)
def download_to_path(self, item_id, ino, dest_path)

# core/downloader.py
def download_process(self):           # Background thread entry point
def process_item(self, item_id)

# core/calibre_import.py
def import_files(gui, file_paths, log)
def is_duplicate(db, mi)

# core/config.py
def save_settings(self)
```

## Plugin Lifecycle

```
1. User clicks button → genesis() called once
2. download_books() on click
3. Authenticate with server (AbsClient.login)
4. Library selection dialog (restore last library IDs)
5. Persist selected library IDs, then fetch items (main thread, wait cursor)
6. Book selection dialog
7. Download dialog: background thread downloads selected items
8. Import to Calibre database (in same thread)
9. Show "Press F5 to see books" message
10. Close dialog
```

## License
GPL v3
