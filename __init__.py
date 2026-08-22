#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import, print_function)
import faulthandler
faulthandler.enable()

__license__ = 'GPL v3'
__copyright__ = '2026, benignpigeon'
__docformat__ = 'restructuredtext en'

from calibre.customize import InterfaceActionBase

class AudiobookshelfDownloaderPlugin(InterfaceActionBase):
    '''
    This plugin downloads ebooks from an Audiobookshelf server
    '''

    name = 'Audiobookshelf Downloader'
    description = 'Download ebooks from your Audiobookshelf server and add them to Calibre'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'benignpigeon'
    version = (1, 0, 3)
    minimum_calibre_version = (1, 0, 3)

    #: This field defines the GUI plugin class that contains all the code
    #: that actually does something. Its format is module_path:class_name
    #: The specified class must be defined in the specified module.
    actual_plugin = 'calibre_plugins.audiobookshelf_downloader.ui:AudiobookshelfDownloaderAction'

    def is_customizable(self):
        '''
        This method must return True to enable customization via
        Preferences->Plugins
        '''
        return True

    def config_widget(self):
        '''
        Implement this method and :meth:`save_settings` in your plugin to
        use a custom configuration dialog.

        This method, if implemented, must return a QWidget. The widget can have
        an optional method validate() that takes no arguments and is called
        immediately after the user clicks OK. Changes are applied if and only
        if the method returns True.

        If for some reason you cannot perform the configuration at this time,
        return a tuple of two strings (message, details), these will be
        displayed as a warning dialog to the user and the process will be
        aborted.
        '''
        from calibre_plugins.audiobookshelf_downloader.config import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        '''
        Save the settings specified by the user with config_widget.

        :param config_widget: The widget returned by :meth:`config_widget`.
        '''
        config_widget.save_settings()
