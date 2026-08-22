#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import, print_function)

__license__ = 'GPL v3'
__copyright__ = '2026, Your Name'
__docformat__ = 'restructuredtext en'

import json
import urllib.request
import urllib.error
import os
import tempfile
from threading import Thread

from PyQt5.Qt import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                      QTextEdit, QProgressBar, QListWidget, QListWidgetItem,
                      QMessageBox, QApplication, Qt, QCheckBox, QMenu, QToolButton,
                      pyqtSignal)
from PyQt5.QtCore import QCoreApplication

from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog
from calibre_plugins.audiobookshelf_downloader.config import prefs

class LibrarySelectDialog(QDialog):
    '''
    Dialog for selecting which libraries to download from
    '''
    def __init__(self, parent, libraries):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Select Libraries')
        self.libraries = libraries
        self.selected_libraries = []
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        label = QLabel('Select libraries to download:')
        self.layout.addWidget(label)
        
        self.list_widget = QListWidget()
        for lib in libraries:
            item = QListWidgetItem(lib['name'])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, lib)
            self.list_widget.addItem(item)
        
        self.layout.addWidget(self.list_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.download_button = QPushButton('Start Download')
        self.download_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.download_button)
        
        self.layout.addLayout(button_layout)
        
        self.resize(400, 300)
    
    def accept(self):
        '''
        Collect selected libraries when user clicks download
        '''
        self.selected_libraries = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                self.selected_libraries.append(item.data(Qt.UserRole))
        
        if not self.selected_libraries:
            error_dialog(self, 'No Libraries Selected', 
                        'Please select at least one library to download.', 
                        show=True)
            return
        
        QDialog.accept(self)

class DownloadDialog(QDialog):
    '''
    Dialog showing download progress and logs
    '''
    # Signal for thread-safe logging - emitted from background thread, received on main thread
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int, int)  # min, max, value
    close_button_signal = pyqtSignal(bool)
    refresh_gui_signal = pyqtSignal()  # Signal to refresh the Calibre GUI
    
    def __init__(self, parent, gui, server_url, username, password, selected_libraries):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Downloading from Audiobookshelf')
        self.gui = gui
        self.server_url = server_url
        self.username = username
        self.password = password
        self.selected_libraries = selected_libraries
        self.token = None
        self.downloaded_files = []
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.status_label = QLabel('Preparing to download...')
        self.layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.layout.addWidget(self.progress_bar)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)
        
        self.close_button = QPushButton('Close')
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        self.layout.addWidget(self.close_button)
        
        self.resize(600, 400)
        
        # Connect signals to slots for thread-safe UI updates
        self.log_signal.connect(self._do_log)
        self.status_signal.connect(self._do_status)
        self.progress_signal.connect(self._do_progress)
        self.close_button_signal.connect(self._do_close_button)
        self.refresh_gui_signal.connect(self._do_refresh_gui)
        
        # Start download in background thread
        self.download_thread = Thread(target=self.safe_download_process)
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def safe_download_process(self):
        '''
        Wrapper for download_process with error handling
        '''
        try:
            self.download_process()
        except Exception as e:
            import traceback
            self.log(f'\n\n💥 CRITICAL ERROR 💥')
            self.log(f'Error: {e}')
            self.log(f'\nFull traceback:\n{traceback.format_exc()}')
            self.status_signal.emit('Critical error occurred!')
            self.progress_signal.emit(0, 1, 1)
            self.close_button_signal.emit(True)
    
    def log(self, message):
        '''
        Add a message to the log - thread-safe via signal
        '''
        self.log_signal.emit(message)
    
    def _do_log(self, message):
        '''
        Slot that performs the actual log update on the main thread
        '''
        self.log_text.append(message)
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        # Process events to flush Qt's text rendering queue and prevent segfaults
        QCoreApplication.processEvents()
    
    def _do_status(self, message):
        '''
        Slot that updates the status label on the main thread
        '''
        self.status_label.setText(message)
        QCoreApplication.processEvents()
    
    def _do_progress(self, min_val, max_val, value):
        '''
        Slot that updates the progress bar on the main thread
        '''
        self.progress_bar.setRange(min_val, max_val)
        self.progress_bar.setValue(value)
        QCoreApplication.processEvents()
    
    def _do_close_button(self, enabled):
        '''
        Slot that enables/disables the close button on the main thread
        '''
        self.close_button.setEnabled(enabled)
        QCoreApplication.processEvents()
    
    def _do_refresh_gui(self):
        '''
        Slot that refreshes the Calibre GUI to show newly added books
        '''
        try:
            # Safely refresh the book list in Calibre
            self.gui.library_view.model().books_added(0)  
            self.gui.library_view.model().refresh()
            self.gui.tags_view.recount()
            QCoreApplication.processEvents()
            self.log('✅ Library view refreshed automatically')
        except Exception as e:
            self.log(f'⚠️  Auto-refresh failed: {e}')
            self.log('   Please press F5 manually to see new books')
    
    def download_process(self):
        '''
        Main download process - runs in background thread
        '''
        try:
            # Authenticate
            self.log('Authenticating with Audiobookshelf...')
            self.authenticate()
            self.log('✓ Authenticated successfully')
            
            # Create temp directory for downloads
            temp_dir = tempfile.mkdtemp(prefix='abs_downloads_')
            self.log(f'Using temporary directory: {temp_dir}')
            
            auth_headers = {
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
            
            # Download from each selected library
            for lib in self.selected_libraries:
                self.log(f'\n--- Scanning library: {lib["name"]} ---')
                
                # Get items in library
                items_url = f"{self.server_url}/api/libraries/{lib['id']}/items"
                items_req = urllib.request.Request(items_url, headers=auth_headers)
                
                with urllib.request.urlopen(items_req) as resp:
                    items_data = json.loads(resp.read().decode())
                    items = items_data.get('results', [])
                
                self.log(f'Found {len(items)} items in {lib["name"]}')
                
                # Process each item
                for item in items:
                    item_id = item.get('id')
                    if not item_id:
                        continue
                    
                    self.process_item(item_id, auth_headers, temp_dir)
            
            self.log(f'\n=== Download Complete ===')
            self.log(f'Downloaded {len(self.downloaded_files)} ebook(s)')
            
            # Import to Calibre if enabled
            if prefs['auto_import'] and self.downloaded_files:
                self.log('\nImporting books to Calibre...')
                try:
                    self.import_to_calibre()
                    self.log('✓ Import complete!')
                except Exception as import_error:
                    import traceback
                    self.log(f'✗ Import failed: {import_error}')
                    self.log(f'Import traceback:\n{traceback.format_exc()}')
            
            self.status_signal.emit('Download complete!')
            self.log('\n✅ Done! Close this window and press F5 to see new books.')
            
        except Exception as e:
            import traceback
            self.log(f'\n✗ Error: {e}')
            self.log(f'Details: {traceback.format_exc()}')
            self.status_signal.emit('Download failed!')
        finally:
            self.progress_signal.emit(0, 1, 1)
            self.close_button_signal.emit(True)
    
    def process_item(self, item_id, auth_headers, temp_dir):
        '''
        Process a single item from the library
        '''
        item_url = f"{self.server_url}/api/items/{item_id}"
        item_req = urllib.request.Request(item_url, headers=auth_headers)
        
        try:
            with urllib.request.urlopen(item_req) as resp:
                details = json.loads(resp.read().decode())
        except Exception as e:
            self.log(f'Could not fetch details for item {item_id}: {e}')
            return
        
        media = details.get('media', {})
        metadata = media.get('metadata', {})
        title = metadata.get('title', 'Unknown')
        
        # Look for ebook files
        files_to_download = []
        
        # Check for ebookFile
        if 'ebookFile' in media and media['ebookFile']:
            files_to_download.append(media['ebookFile'])
        
        # Check in libraryFiles for ebooks
        if 'libraryFiles' in media:
            for f in media['libraryFiles']:
                file_type = f.get('fileType', '')
                if file_type == 'ebook' or self.is_ebook_file(f.get('metadata', {}).get('filename', '')):
                    files_to_download.append(f)
        
        # Download ebook files
        for f in files_to_download:
            self.download_file(f, item_id, title, auth_headers, temp_dir)
    
    def download_file(self, f, item_id, title, auth_headers, temp_dir):
        '''
        Download a single file
        '''
        ino = f.get('ino')
        metadata_obj = f.get('metadata', {})
        fname = metadata_obj.get('filename') or f.get('filename') or os.path.basename(f.get('path', ''))
        
        if not fname:
            return
        
        self.log(f'Downloading: {fname} (from "{title}")')
        
        # Construct download URL
        if ino:
            dl_url = f"{self.server_url}/api/items/{item_id}/file/{ino}/download"
        else:
            dl_url = f"{self.server_url}/api/items/{item_id}/download"
        
        dl_req = urllib.request.Request(dl_url, headers=auth_headers)
        
        try:
            dest_path = os.path.join(temp_dir, fname)
            with urllib.request.urlopen(dl_req) as dl_resp, open(dest_path, 'wb') as out_file:
                while True:
                    chunk = dl_resp.read(16384)
                    if not chunk:
                        break
                    out_file.write(chunk)
            
            self.log(f'✓ Downloaded: {fname}')
            self.downloaded_files.append(dest_path)
        except Exception as e:
            self.log(f'✗ Failed to download {fname}: {e}')
    
    def authenticate(self):
        '''
        Authenticate with Audiobookshelf server
        '''
        login_url = f"{self.server_url}/login"
        login_data = json.dumps({
            "username": self.username,
            "password": self.password
        }).encode('utf-8')
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        
        req = urllib.request.Request(
            login_url,
            data=login_data,
            headers=headers
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                self.token = result.get('user', {}).get('token')
                
                if not self.token:
                    raise Exception('No token received from server')
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='ignore')
            raise Exception(f'Authentication failed: {e.code} - {error_body}')
    
    def is_ebook_file(self, filename):
        '''
        Check if filename is an ebook based on extension
        '''
        ebook_extensions = ['.epub', '.pdf', '.mobi', '.azw', '.azw3', '.fb2', '.cbz', '.cbr', '.txt']
        return any(filename.lower().endswith(ext) for ext in ebook_extensions)
    
    def import_to_calibre(self):
        '''
        Import downloaded files to Calibre library
        '''
        if not self.downloaded_files:
            return
        
        try:
            from calibre.ebooks.metadata.meta import get_metadata
            
            db = self.gui.current_db
            added_count = 0
            skipped_count = 0
            
            for file_path in self.downloaded_files:
                try:
                    if not os.path.exists(file_path):
                        self.log(f'✗ File not found: {os.path.basename(file_path)}')
                        continue
                    
                    # Get metadata from file
                    with open(file_path, 'rb') as f:
                        ext = os.path.splitext(file_path)[1][1:].lower()
                        if not ext:
                            self.log(f'Skipping file with no extension: {os.path.basename(file_path)}')
                            continue
                        mi = get_metadata(f, ext)
                    
                    # Check for duplicates if enabled
                    if prefs.get('skip_duplicates', True):
                        if self.is_duplicate(db, mi):
                            self.log(f'⊘ Skipped (already in library): {mi.title or os.path.basename(file_path)}')
                            skipped_count += 1
                            continue
                    
                    # Add to database
                    book_id = db.add_books([file_path], [ext], [mi])[0]
                    added_count += 1
                    self.log(f'✓ Added to Calibre: {mi.title or os.path.basename(file_path)}')
                    
                except Exception as e:
                    self.log(f'✗ Failed to import {os.path.basename(file_path)}: {e}')
            
            # Summary
            self.log(f'\n📊 Import Summary: {added_count} added, {skipped_count} skipped')
            
            # Trigger GUI refresh if books were added
            if added_count > 0:
                self.log('')
                self.log('🔄 Refreshing library view...')
                self.refresh_gui_signal.emit()
                    
        except Exception as e:
            import traceback
            self.log(f'✗ Import error: {e}')
            self.log(f'Traceback: {traceback.format_exc()}')
    
    def is_duplicate(self, db, mi):
        '''
        Check if book already exists in library
        '''
        try:
            if not mi.title:
                return False
            
            # Search for books with same title
            search_results = db.search_getting_ids(f'title:"{mi.title}"', '')
            
            if not search_results:
                return False
            
            # If we have author info, check author too
            if mi.authors:
                for book_id in search_results:
                    existing_mi = db.get_metadata(book_id)
                    if existing_mi.authors and mi.authors:
                        # Compare author names (case insensitive)
                        existing_authors = {a.lower() for a in existing_mi.authors}
                        new_authors = {a.lower() for a in mi.authors}
                        if existing_authors & new_authors:  # If any author matches
                            return True
            else:
                # No author info, just matching title is enough
                return True
                
            return False
        except:
            return False

class AudiobookshelfDownloaderAction(InterfaceAction):
    '''
    Main action for the Audiobookshelf Downloader plugin
    '''
    name = 'Audiobookshelf Downloader'
    
    # Declares the main action associated with this plugin
    # Format: (name, icon_path, tooltip, keyboard_shortcut)
    action_spec = ('Audiobookshelf Downloader', None,
                   'Download ebooks from Audiobookshelf', None)
    
    action_type = 'current'
    popup_type = QToolButton.MenuButtonPopup
    
    def genesis(self):
        '''
        This method is called once per plugin, do initial setup here
        '''
        # Load and set icon
        icon = get_icons('images/abs_icon.png')
        self.qaction.setIcon(icon)
        
        # Store the icon for menu items
        self.plugin_icon = icon
        
        # Create menu
        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)
        
        # Add main action
        self.qaction.triggered.connect(self.download_books)
        
        # Add menu items
        self.create_menu_actions()
    
    def create_menu_actions(self):
        '''
        Create dropdown menu actions
        '''
        from PyQt5.Qt import QAction
        
        # Configure action
        config_action = QAction('Configure...', self.gui)
        config_action.triggered.connect(self.show_configuration)
        self.menu.addAction(config_action)
        
        self.menu.addSeparator()
        
        # Download action
        download_action = QAction('Download Books', self.gui)
        download_action.triggered.connect(self.download_books)
        self.menu.addAction(download_action)
    
    def show_configuration(self):
        '''
        Open the plugin configuration dialog
        '''
        self.interface_action_base_plugin.do_user_config(self.gui)
    
    def download_books(self):
        '''
        Main download action - check config and start download
        '''
        # Check if credentials are configured
        if not prefs['server_url'] or not prefs['username'] or not prefs['password']:
            from PyQt5.Qt import QMessageBox
            result = QMessageBox.question(
                self.gui, 
                'Configuration Required',
                'Audiobookshelf server settings are not configured.\n\n'
                'Would you like to configure them now?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if result == QMessageBox.Yes:
                self.show_configuration()
            return
        
        try:
            # Authenticate and get libraries
            server_url = prefs['server_url']
            username = prefs['username']
            password = prefs['password']
            
            # Authenticate
            token = self.authenticate(server_url, username, password)
            
            # Get libraries
            libraries = self.get_libraries(server_url, token)
            
            if not libraries:
                info_dialog(self.gui, 'No Libraries Found',
                          'No libraries found on the server.',
                          show=True)
                return
            
            # Show library selection dialog
            dialog = LibrarySelectDialog(self.gui, libraries)
            if dialog.exec_() == QDialog.Accepted:
                selected_libraries = dialog.selected_libraries
                
                if selected_libraries:
                    # Show download dialog
                    download_dialog = DownloadDialog(self.gui, self.gui, server_url, 
                                                    username, password, selected_libraries)
                    download_dialog.exec_()
        
        except Exception as e:
            error_dialog(self.gui, 'Error',
                        f'Failed to connect to Audiobookshelf:<br><br>{str(e)}',
                        show=True)
    
    def authenticate(self, server_url, username, password):
        '''
        Authenticate with server and return token
        '''
        login_url = f"{server_url}/login"
        login_data = json.dumps({
            "username": username,
            "password": password
        }).encode('utf-8')
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        
        req = urllib.request.Request(
            login_url,
            data=login_data,
            headers=headers
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                token = result.get('user', {}).get('token')
                
                if not token:
                    raise Exception('No token received from server')
                
                return token
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8', errors='ignore')
            raise Exception(f'Authentication failed: {e.code} - {error_body}')
    
    def get_libraries(self, server_url, token):
        '''
        Get list of libraries from server
        '''
        libraries_url = f"{server_url}/api/libraries"
        headers = {
            'Authorization': f'Bearer {token}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        req = urllib.request.Request(libraries_url, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            libraries = data.get('libraries', [])
            return libraries
    
    def apply_settings(self):
        '''
        Apply settings after configuration
        '''
        pass

def get_icons(icon_name):
    '''
    Load plugin icon from images directory
    '''
    import os
    from PyQt5.Qt import QIcon, QPixmap
    
    try:
        # Try to get icon from plugin resources
        from calibre.utils.zipfile import ZipFile
        from calibre.customize.ui import find_plugin
        
        # Find this plugin
        plugin = find_plugin('Audiobookshelf Downloader')
        if plugin:
            plugin_path = plugin.plugin_path
            if plugin_path and os.path.exists(plugin_path):
                # If it's a zip file, extract the icon
                if plugin_path.endswith('.zip'):
                    with ZipFile(plugin_path, 'r') as zf:
                        if icon_name in zf.namelist():
                            icon_data = zf.read(icon_name)
                            pixmap = QPixmap()
                            pixmap.loadFromData(icon_data)
                            if not pixmap.isNull():
                                return QIcon(pixmap)
                else:
                    # If it's extracted, load directly
                    icon_path = os.path.join(os.path.dirname(plugin_path), icon_name)
                    if os.path.exists(icon_path):
                        pixmap = QPixmap(icon_path)
                        if not pixmap.isNull():
                            return QIcon(pixmap)
    except Exception as e:
        print(f"Icon loading error: {e}")
        pass
    
    # Try from __file__ location
    try:
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(plugin_dir, icon_name)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                return QIcon(pixmap)
    except:
        pass
    
    # Fallback to calibre default icon
    try:
        from calibre.gui2 import get_icons as get_calibre_icons
        return get_calibre_icons('download-metadata.png')
    except:
        return QIcon()
