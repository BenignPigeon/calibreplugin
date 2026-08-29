#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import, print_function)

__license__ = 'GPL v3'
__copyright__ = '2026, benignpigeon'
__docformat__ = 'restructuredtext en'

from PyQt5.Qt import (QAction, QApplication, QDialog, QMenu, QMessageBox, Qt, QToolButton)

from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog
from calibre_plugins.audiobookshelf_downloader.core.config import prefs
from calibre_plugins.audiobookshelf_downloader.core.api import AbsClient, normalize_item
from calibre_plugins.audiobookshelf_downloader.core.select_dialogs import (LibrarySelectDialog, ItemSelectDialog)
from calibre_plugins.audiobookshelf_downloader.core.downloader import DownloadDialog


class AudiobookshelfDownloaderAction(InterfaceAction):
    '''
    Toolbar button, dropdown menu, and flow routing.
    '''
    name = 'Audiobookshelf Downloader'

    action_spec = ('Audiobookshelf', None,
                   'Download ebooks from Audiobookshelf', None)

    action_type = 'current'
    popup_type = QToolButton.MenuButtonPopup

    def genesis(self):
        icon = get_icons('images/abs_icon.png', 'Audiobookshelf Downloader')
        self.qaction.setIcon(icon)

        self.menu = QMenu(self.gui)
        self.qaction.setMenu(self.menu)

        self.qaction.triggered.connect(self.download_books)
        self.create_menu_actions()

    def create_menu_actions(self):
        config_action = QAction('Configure...', self.gui)
        config_action.triggered.connect(self.show_configuration)
        self.menu.addAction(config_action)

        self.menu.addSeparator()

        download_action = QAction('Download Books', self.gui)
        download_action.triggered.connect(self.download_books)
        self.menu.addAction(download_action)

    def show_configuration(self):
        self.interface_action_base_plugin.do_user_config(self.gui)

    def download_books(self):
        if not prefs['server_url'] or not prefs['username'] or not prefs['password']:
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
            client = AbsClient(prefs['server_url'])
            client.login(prefs['username'], prefs['password'])

            libraries = client.get_libraries()
            if not libraries:
                info_dialog(
                    self.gui, 'No Libraries Found',
                    'No libraries found on the server.',
                    show=True
                )
                return

            library_dialog = LibrarySelectDialog(
                self.gui, libraries, prefs['selected_library_ids']
            )
            if library_dialog.exec_() != QDialog.Accepted:
                return

            selected_libraries = library_dialog.selected_libraries
            prefs['selected_library_ids'] = [
                lib.get('id') for lib in selected_libraries if lib.get('id')
            ]
            items = self._load_items(client, selected_libraries)
            if items is None:
                return

            if not items:
                info_dialog(
                    self.gui, 'No Books Found',
                    'No books found in the selected libraries.',
                    show=True
                )
                return

            item_dialog = ItemSelectDialog(self.gui, items)
            if item_dialog.exec_() != QDialog.Accepted:
                return

            download_dialog = DownloadDialog(
                self.gui, client, item_dialog.selected_items
            )
            download_dialog.exec_()

        except Exception as e:
            error_dialog(
                self.gui, 'Error',
                f'Failed to connect to Audiobookshelf:<br><br>{str(e)}',
                show=True
            )

    def _load_items(self, client, selected_libraries):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            items = []
            for lib in selected_libraries:
                raw_items = client.get_library_items(lib['id'])
                library_name = lib.get('name') or ''
                for raw in raw_items:
                    normalized = normalize_item(raw, library_name)
                    if normalized.get('id'):
                        items.append(normalized)
            return items
        except Exception as e:
            error_dialog(
                self.gui, 'Error',
                f'Failed to load books from Audiobookshelf:<br><br>{str(e)}',
                show=True
            )
            return None
        finally:
            QApplication.restoreOverrideCursor()

    def apply_settings(self):
        pass
