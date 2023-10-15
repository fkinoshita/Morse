# SPDX-License-Identifier: GPL-3.0-only

import re
from gi.repository import Adw, Gtk, Gdk, Gio, GLib

from .const import PROFILE
from .utils import Utils

@Gtk.Template(resource_path='/io/github/fkinoshita/Telegraph/ui/window.ui')
class TelegraphWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'TelegraphWindow'

    toast_overlay = Gtk.Template.Child()

    message_group = Gtk.Template.Child()
    morse_group = Gtk.Template.Child()

    message_text_view = Gtk.Template.Child()
    morse_text_view = Gtk.Template.Child()

    message_copy_button = Gtk.Template.Child()
    morse_copy_button = Gtk.Template.Child()


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if PROFILE == 'Devel':
            self.add_css_class('devel')

        self.connect('unrealize', self.save_settings)

        self.settings = Gio.Settings.new(Gio.Application.get_default().get_application_id())

        self.load_settings()

        self.set_size_request(320, 450)

        self.message_buffer = self.message_text_view.get_buffer()
        self.message_buffer.connect('changed', self.__on_input_changed)

        self.morse_buffer = self.morse_text_view.get_buffer()
        self.morse_buffer.connect('changed', self.__on_input_changed)

        self.message_copy_button.connect('clicked', self.__on_copy_button_clicked)
        self.morse_copy_button.connect('clicked', self.__on_copy_button_clicked)

        self.updated_buffer = None
        self.timeout_buffer = 0

        self.message_text_view.get_buffer().set_text("SOS")
        self.message_text_view.grab_focus()


    def __on_input_changed(self, input_buffer):
        if self.timeout_buffer > 0 and input_buffer == self.updated_buffer:
            self.timeout_buffer -= 1
            self.updated_buffer = None if self.timeout_buffer == 0 else self.updated_buffer
            return

        (start, end) = input_buffer.get_bounds()
        text = input_buffer.get_text(start, end, False)

        if input_buffer == self.message_buffer:
            output_message = Utils.translate_to(text)

            self.timeout_buffer = 2
            self.updated_buffer = self.morse_buffer
            self.morse_buffer.set_text(output_message)

        elif input_buffer == self.morse_buffer:
            output_message = Utils.translate_from(text)

            self.timeout_buffer = 2
            self.updated_buffer = self.message_buffer
            self.message_buffer.set_text(output_message)

        (start, end) = self.morse_buffer.get_bounds()
        morse_output = self.morse_buffer.get_text(start, end, False)

        (start, end) = self.message_buffer.get_bounds()
        text_output = self.message_buffer.get_text(start, end, False)

        if len(text_output) == 0:
            self.message_copy_button.set_sensitive(False)
        else:
            self.message_copy_button.set_sensitive(True)

        if len(morse_output) == 0:
            self.morse_copy_button.set_sensitive(False)
        else:
            self.morse_copy_button.set_sensitive(True)


    def __on_copy_button_clicked(self, button):
        self.copy(button)


    def copy(self, button):
        toast = Adw.Toast()

        if button == self.message_copy_button:
            output_buffer = self.message_text_view.get_buffer()
            toast.set_title(_('Message copied'))

        elif button == self.morse_copy_button:
            output_buffer = self.morse_text_view.get_buffer()
            toast.set_title(_('Morse code copied'))

        (start, end) = output_buffer.get_bounds()
        output = output_buffer.get_text(start, end, False)

        if (len(output) == 0):
            return

        Gdk.Display.get_default().get_clipboard().set(output)

        self.toast_overlay.add_toast(toast)


    def save_settings(self, *args, **kwargs):
        width, height = self.get_default_size()
        size = [width, height]
        size = GLib.Variant('ai', list(size))
        Gio.Settings.set_value(self.settings, 'window-size', size)


    def load_settings(self):
        size = Gio.Settings.get_value(self.settings, 'window-size')
        self.set_default_size(size[0], size[1])

