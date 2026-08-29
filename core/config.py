#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import, print_function)

__license__ = 'GPL v3'
__copyright__ = '2026, benignpigeon'
__docformat__ = 'restructuredtext en'

from PyQt5.Qt import (QWidget, QVBoxLayout, QLabel, QLineEdit, QCheckBox,
                      QGroupBox, QFormLayout)

from calibre.utils.config import JSONConfig

# This is where your plugins preferences will be stored
prefs = JSONConfig('plugins/audiobookshelf_downloader')

# Set defaults
prefs.defaults['server_url'] = 'https://audiobookshelf.example.com'
prefs.defaults['username'] = ''
prefs.defaults['password'] = ''
prefs.defaults['auto_import'] = True
prefs.defaults['skip_duplicates'] = True
prefs.defaults['selected_library_ids'] = []


class ConfigWidget(QWidget):
    '''
    Configuration widget for the Audiobookshelf Downloader plugin
    '''

    def __init__(self):
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Server Settings Group
        server_group = QGroupBox('Audiobookshelf Server Settings')
        server_layout = QFormLayout()

        # Force form fields to expand and fill the container width
        server_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        server_group.setLayout(server_layout)

        self.server_url_edit = QLineEdit(self)
        self.server_url_edit.setText(prefs['server_url'])
        self.server_url_edit.setToolTip('The URL of your Audiobookshelf server (e.g., https://audiobookshelf.example.com)')
        server_layout.addRow('Server URL:', self.server_url_edit)

        self.username_edit = QLineEdit(self)
        self.username_edit.setText(prefs['username'])
        self.username_edit.setToolTip('Your Audiobookshelf username')
        server_layout.addRow('Username:', self.username_edit)

        self.password_edit = QLineEdit(self)
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setText(prefs['password'])
        self.password_edit.setToolTip('Your Audiobookshelf password')
        server_layout.addRow('Password:', self.password_edit)

        self.layout.addWidget(server_group)

        # Options Group
        options_group = QGroupBox('Options')
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)

        self.auto_import_checkbox = QCheckBox('Automatically add downloaded books to Calibre')
        self.auto_import_checkbox.setChecked(prefs['auto_import'])
        self.auto_import_checkbox.setToolTip('When checked, downloaded books will be automatically added to your Calibre library')
        options_layout.addWidget(self.auto_import_checkbox)

        self.skip_duplicates_checkbox = QCheckBox('Skip books already in library (recommended)')
        self.skip_duplicates_checkbox.setChecked(prefs['skip_duplicates'])
        self.skip_duplicates_checkbox.setToolTip('When checked, books with matching title and author will not be re-imported')
        options_layout.addWidget(self.skip_duplicates_checkbox)

        self.layout.addWidget(options_group)

        # Info Label
        info_label = QLabel('Note: Your credentials are stored securely in Calibre\'s configuration.')
        info_label.setWordWrap(True)
        info_label.setStyleSheet('color: gray; font-style: italic; margin-top: 10px;')
        self.layout.addWidget(info_label)

        self.layout.addStretch()

    def save_settings(self):
        '''
        Save the settings specified by the user
        '''
        prefs['server_url'] = self.server_url_edit.text().rstrip('/')
        prefs['username'] = self.username_edit.text()
        prefs['password'] = self.password_edit.text()
        prefs['auto_import'] = self.auto_import_checkbox.isChecked()
        prefs['skip_duplicates'] = self.skip_duplicates_checkbox.isChecked()

    def validate(self):
        '''
        Validate the settings
        '''
        if not self.server_url_edit.text():
            return False
        if not self.username_edit.text():
            return False
        if not self.password_edit.text():
            return False
        return True
