#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import, print_function)

__license__ = 'GPL v3'
__copyright__ = '2026, benignpigeon'
__docformat__ = 'restructuredtext en'

import os
import tempfile
from threading import Thread

from PyQt5.Qt import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QProgressBar, pyqtSignal
)
from PyQt5.QtCore import QCoreApplication

from .config import prefs
from .calibre_import import import_files


EBOOK_EXTENSIONS = ['.epub', '.pdf', '.mobi', '.azw', '.azw3', '.fb2', '.cbz', '.cbr', '.txt']


class DownloadDialog(QDialog):
    '''
    Dialog showing download progress and logs.
    Downloads only the items chosen in ItemSelectDialog.
    '''
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int, int)
    close_button_signal = pyqtSignal(bool)
    refresh_gui_signal = pyqtSignal()

    def __init__(self, parent, gui, client, selected_items):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Downloading from Audiobookshelf')
        self.gui = gui
        self.client = client
        self.selected_items = selected_items
        self.downloaded_files = []
        self.temp_dir = None

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.status_label = QLabel('Preparing to download...')
        self.layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.layout.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.layout.addWidget(self.log_text)

        self.close_button = QPushButton('Close')
        self.close_button.setEnabled(False)
        self.close_button.clicked.connect(self.accept)
        self.layout.addWidget(self.close_button)

        self.resize(600, 400)

        self.log_signal.connect(self._do_log)
        self.status_signal.connect(self._do_status)
        self.progress_signal.connect(self._do_progress)
        self.close_button_signal.connect(self._do_close_button)
        self.refresh_gui_signal.connect(self._do_refresh_gui)

        self.download_thread = Thread(target=self.safe_download_process)
        self.download_thread.daemon = True
        self.download_thread.start()

    def safe_download_process(self):
        try:
            self.download_process()
        except Exception as e:
            import traceback
            self.log('\n\n💥 CRITICAL ERROR 💥')
            self.log(f'Error: {e}')
            self.log(f'\nFull traceback:\n{traceback.format_exc()}')
            self.status_signal.emit('Critical error occurred!')
            self.progress_signal.emit(0, 1, 1)
            self.close_button_signal.emit(True)

    def log(self, message):
        self.log_signal.emit(message)

    def _do_log(self, message):
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        QCoreApplication.processEvents()

    def _do_status(self, message):
        self.status_label.setText(message)
        QCoreApplication.processEvents()

    def _do_progress(self, min_val, max_val, value):
        self.progress_bar.setRange(min_val, max_val)
        self.progress_bar.setValue(value)
        QCoreApplication.processEvents()

    def _do_close_button(self, enabled):
        self.close_button.setEnabled(enabled)
        QCoreApplication.processEvents()

    def _do_refresh_gui(self):
        try:
            self.gui.library_view.model().books_added(0)
            self.gui.library_view.model().refresh()
            self.gui.tags_view.recount()
            QCoreApplication.processEvents()
            self.log('✅ Library view refreshed automatically')
        except Exception as e:
            self.log(f'⚠️  Auto-refresh failed: {e}')
            self.log('   Please press F5 manually to see new books')

    def download_process(self):
        try:
            self.temp_dir = tempfile.mkdtemp(prefix='abs_downloads_')
            self.log(f'Using temporary directory: {self.temp_dir}')
            self.log(f'Downloading {len(self.selected_items)} selected book(s)')

            total = len(self.selected_items)
            self.progress_signal.emit(0, max(total, 1), 0)

            for index, item in enumerate(self.selected_items, start=1):
                item_id = item.get('id')
                if not item_id:
                    continue
                title = item.get('title') or 'Unknown'
                self.status_signal.emit(f'Downloading {index}/{total}: {title}')
                self.process_item(item_id)
                self.progress_signal.emit(0, max(total, 1), index)

            self.log('\n=== Download Complete ===')
            self.log(f'Downloaded {len(self.downloaded_files)} ebook(s)')

            if prefs['auto_import'] and self.downloaded_files:
                self.log('\nImporting books to Calibre...')
                try:
                    added_count = import_files(self.gui, self.downloaded_files, self.log)
                    self.log('✓ Import complete!')
                    if added_count > 0:
                        self.log('')
                        self.log('🔄 Refreshing library view...')
                        self.refresh_gui_signal.emit()
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

    def process_item(self, item_id):
        try:
            details = self.client.get_item(item_id)
        except Exception as e:
            self.log(f'Could not fetch details for item {item_id}: {e}')
            return

        media = details.get('media', {})
        metadata = media.get('metadata', {})
        title = metadata.get('title', 'Unknown')

        files_to_download = []

        if media.get('ebookFile'):
            files_to_download.append(media['ebookFile'])

        if 'libraryFiles' in media:
            for f in media['libraryFiles']:
                file_type = f.get('fileType', '')
                filename = f.get('metadata', {}).get('filename', '')
                if file_type == 'ebook' or self.is_ebook_file(filename):
                    files_to_download.append(f)

        for f in files_to_download:
            self.download_file(f, item_id, title)

    def download_file(self, f, item_id, title):
        ino = f.get('ino')
        metadata_obj = f.get('metadata', {})
        fname = metadata_obj.get('filename') or f.get('filename') or os.path.basename(f.get('path', ''))

        if not fname:
            return

        self.log(f'Downloading: {fname} (from "{title}")')
        dest_path = os.path.join(self.temp_dir, fname)

        try:
            self.client.download_to_path(item_id, ino, dest_path)
            self.log(f'✓ Downloaded: {fname}')
            self.downloaded_files.append(dest_path)
        except Exception as e:
            self.log(f'✗ Failed to download {fname}: {e}')

    def is_ebook_file(self, filename):
        return any(filename.lower().endswith(ext) for ext in EBOOK_EXTENSIONS)
