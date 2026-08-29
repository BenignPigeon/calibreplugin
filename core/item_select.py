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


def _item_display_text(item):
    title = item.get('title') or 'Unknown'
    author = item.get('author') or ''
    library_name = item.get('library_name') or ''
    if author and library_name:
        return f'{title} — {author} ({library_name})'
    if author:
        return f'{title} — {author}'
    if library_name:
        return f'{title} ({library_name})'
    return title


class ItemSelectDialog(QDialog):
    '''
    Dialog for selecting which books to download
    '''

    def __init__(self, parent, items):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Select Books')
        self.items = items
        self.selected_items = []

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        label = QLabel('Select books to download:')
        self.layout.addWidget(label)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Search by title or author...')
        self.search_edit.textChanged.connect(self._apply_filter)
        self.layout.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        for book in items:
            if not book.get('id'):
                continue
            list_item = QListWidgetItem(_item_display_text(book))
            list_item.setFlags(list_item.flags() | Qt.ItemIsUserCheckable)
            list_item.setCheckState(Qt.Checked)
            list_item.setData(Qt.UserRole, book)
            self.list_widget.addItem(list_item)

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
        self.download_button = QPushButton('Download Selected')
        self.download_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.download_button)

        self.layout.addLayout(button_layout)

        self.resize(560, 480)

    def _apply_filter(self, text):
        query = (text or '').strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not query:
                item.setHidden(False)
                continue
            book = item.data(Qt.UserRole) or {}
            haystack = ' '.join([
                item.text(),
                book.get('title') or '',
                book.get('author') or '',
                book.get('library_name') or '',
            ]).lower()
            item.setHidden(query not in haystack)

    def _set_visible_check_state(self, state):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item.isHidden():
                item.setCheckState(state)

    def accept(self):
        self.selected_items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.Checked:
                self.selected_items.append(item.data(Qt.UserRole))

        if not self.selected_items:
            error_dialog(
                self, 'No Books Selected',
                'Please select at least one book to download.',
                show=True
            )
            return

        QDialog.accept(self)
