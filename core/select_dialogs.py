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


class CheckableListDialog(QDialog):
    '''
    Searchable checkbox list. Select All/None and accept() apply to
    visible rows only so a filter cannot silently include hidden items.
    '''

    def __init__(
        self, parent, window_title, prompt, search_placeholder,
        accept_label, empty_title, empty_message, size
    ):
        QDialog.__init__(self, parent)
        self.setWindowTitle(window_title)
        self._empty_title = empty_title
        self._empty_message = empty_message
        self.selected = []

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel(prompt))

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(search_placeholder)
        self.search_edit.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        select_layout = QHBoxLayout()
        select_all_button = QPushButton('Select All')
        select_all_button.setAutoDefault(False)
        select_all_button.clicked.connect(
            lambda: self._set_visible_check_state(Qt.Checked)
        )
        select_none_button = QPushButton('Select None')
        select_none_button.setAutoDefault(False)
        select_none_button.clicked.connect(
            lambda: self._set_visible_check_state(Qt.Unchecked)
        )
        select_layout.addWidget(select_all_button)
        select_layout.addWidget(select_none_button)
        select_layout.addStretch()
        layout.addLayout(select_layout)

        button_layout = QHBoxLayout()
        accept_button = QPushButton(accept_label)
        accept_button.setDefault(True)
        accept_button.clicked.connect(self.accept)
        cancel_button = QPushButton('Cancel')
        cancel_button.setAutoDefault(False)
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(accept_button)
        layout.addLayout(button_layout)

        self.resize(*size)

    def add_checkable_item(self, text, data, checked=True):
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        item.setData(Qt.UserRole, data)
        self.list_widget.addItem(item)

    def _apply_filter(self, text):
        query = (text or '').strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(bool(query) and query not in item.text().lower())

    def _set_visible_check_state(self, state):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item.isHidden():
                item.setCheckState(state)

    def checked_visible_data(self):
        selected = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if not item.isHidden() and item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected

    def accept(self):
        self.selected = self.checked_visible_data()
        if not self.selected:
            error_dialog(
                self, self._empty_title, self._empty_message, show=True
            )
            return
        QDialog.accept(self)


class LibrarySelectDialog(CheckableListDialog):
    def __init__(self, parent, libraries, previously_selected_ids=None):
        CheckableListDialog.__init__(
            self, parent,
            'Select Libraries',
            'Select libraries to browse:',
            'Search libraries...',
            'Next',
            'No Libraries Selected',
            'Please select at least one library.',
            (400, 360),
        )
        remembered_ids = set(previously_selected_ids or [])
        restore = bool(remembered_ids) and any(
            lib.get('id') in remembered_ids for lib in libraries
        )
        for lib in libraries:
            checked = True if not restore else lib.get('id') in remembered_ids
            self.add_checkable_item(lib['name'], lib, checked)

    @property
    def selected_libraries(self):
        return self.selected


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


class ItemSelectDialog(CheckableListDialog):
    def __init__(self, parent, items):
        CheckableListDialog.__init__(
            self, parent,
            'Select Books',
            'Select books to download:',
            'Search by title or author...',
            'Download Selected',
            'No Books Selected',
            'Please select at least one book to download.',
            (560, 480),
        )
        for book in items:
            if book.get('id'):
                self.add_checkable_item(_item_display_text(book), book, True)

    @property
    def selected_items(self):
        return self.selected
