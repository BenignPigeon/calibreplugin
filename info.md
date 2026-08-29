# Coding files

- `__init__.py` — Calibre plugin entry (metadata, config hooks, faulthandler). Required at zip root.
- `main.py` — Toolbar action and download flow (login → pick libraries → pick books → download).
- `build_plugin.py` — Zips the plugin and syncs `__init__.py` version from `version.txt`.
- `core/__init__.py` — Marks `core` as a package so Calibre can import the modules.
- `core/config.py` — Settings UI and `JSONConfig` prefs (server, import options, last library IDs).
- `core/api.py` — Audiobookshelf HTTP client (auth, libraries, items, file download).
- `core/select_dialogs.py` — Shared checkbox-list dialog plus library and book pickers.
- `core/downloader.py` — Progress UI and background download/import thread.
- `core/calibre_import.py` — Duplicate check and `add_books` into the Calibre library.
