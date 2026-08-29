#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import, print_function)

__license__ = 'GPL v3'
__copyright__ = '2026, benignpigeon'
__docformat__ = 'restructuredtext en'

import os

from .config import prefs


def is_duplicate(db, mi):
    '''
    Check if book already exists in library using thread-safe new_api
    '''
    try:
        if not mi.title:
            return False

        api = db.new_api

        search_expr = f'title:"={mi.title}"'
        try:
            search_results = api.search(search_expr)
        except Exception:
            search_expr = f'title:"{mi.title}"'
            search_results = api.search(search_expr)

        if not search_results:
            return False

        if mi.authors:
            for book_id in search_results:
                existing_mi = api.get_metadata(book_id)
                if existing_mi.authors and mi.authors:
                    existing_authors = {a.lower() for a in existing_mi.authors}
                    new_authors = {a.lower() for a in mi.authors}
                    if existing_authors & new_authors:
                        return True
        else:
            return True

        return False
    except Exception as e:
        print(f'[Audiobookshelf] Duplicate check failed: {e}')
        return False


def import_files(gui, file_paths, log):
    '''
    Import downloaded files into the current Calibre library.

    :param log: callable that accepts a string (thread-safe logger)
    :return: number of books added
    '''
    if not file_paths:
        return 0

    from calibre.ebooks.metadata.meta import get_metadata

    db = gui.current_db
    added_count = 0
    skipped_count = 0

    for file_path in file_paths:
        try:
            if not os.path.exists(file_path):
                log(f'✗ File not found: {os.path.basename(file_path)}')
                continue

            with open(file_path, 'rb') as f:
                ext = os.path.splitext(file_path)[1][1:].lower()
                if not ext:
                    log(f'Skipping file with no extension: {os.path.basename(file_path)}')
                    continue
                mi = get_metadata(f, ext)

            if prefs.get('skip_duplicates', True):
                if is_duplicate(db, mi):
                    log(f'⊘ Skipped (already in library): {mi.title or os.path.basename(file_path)}')
                    skipped_count += 1
                    continue

            db.add_books([file_path], [ext], [mi])
            added_count += 1
            log(f'✓ Added to Calibre: {mi.title or os.path.basename(file_path)}')

        except Exception as e:
            log(f'✗ Failed to import {os.path.basename(file_path)}: {e}')

    log(f'\n📊 Import Summary: {added_count} added, {skipped_count} skipped')
    return added_count
