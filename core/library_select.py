#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import, print_function)

__license__ = 'GPL v3'
__copyright__ = '2026, benignpigeon'
__docformat__ = 'restructuredtext en'

from PyQt5.Qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, Qt
)

from calibre.gui2 import error_dialog


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

        label = QLabel('Select libraries to browse:')
        self.layout.addWidget(label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Search libraries...')
        self.search_edit.textChanged.connect(self._apply_filter)
        self.layout.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        for lib in libraries:
            item = QListWidgetItem(lib['name'])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setData(Qt.UserRole, lib)
            self.list_widget.addItem(item)

        self.layout.addWidget(self.list_widget)

        select_layout = QHBoxLayout()
        select_all_button = QPushButton('Select All')
        select_all_button.clicked.connect(lambda: self._set_visible_check_state(Qt.Checked))
        select_none_button = QPushButton('Select None')
        select_none_button.clicked.connect(lambda: self._set_visible_check_state(Qt.Unchecked))
        select_layout.addWidget(select_all_button)
        select_layout.addWidget(select_none_button)
        select_layout.addStretch()
        self.layout.addLayout(select_layout)

        button_layout = QHBoxLayout()
        self.next_button = QPushButton('Next')
        self.next_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.next_button)

        self.layout.addLayout(button_layout)

        self.resize(400, 360)

    def _apply_filter(self, text):
        query = (text or '').strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not query:
                item.setHidden(False)
                continue
            item.setHidden(query not in item.text().lower())

    def _set_visible_check_state(self, state):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item.isHidden():
                item.setCheckState(state)

    def accept(self):
        self.selected_libraries = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                self.selected_libraries.append(item.data(Qt.UserRole))

        if not self.selected_libraries:
            error_dialog(
                self, 'No Libraries Selected',
                'Please select at least one library.',
                show=True
            )
            return

        QDialog.accept(self)
