#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import os
import time
import subprocess
import threading

# Renamed in Python 2.6
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import gtk
import gobject
import glib

import reddit

# Needed to display notifications when a new message comes in.
# Without, the icon will just change.
try:
    import pynotify
except ImportError:
    pynotify = None

# We can display a custom tooltip if egg.trayicon is available.
# Install python-gnome2-extras to get it.
try:
    import egg.trayicon
except ImportError:
    egg.trayicon = None


UI_DEFINITION           = os.path.abspath('reddit_tray_icon.ui')
REDDIT_ICON             = os.path.abspath('icons/reddit.png')
NEW_MAIL_ICON           = os.path.abspath('icons/new_mail.png')
BUSY_ICON               = os.path.abspath('icons/busy.gif')
DEFAULT_USERNAME        = ''
DEFAULT_PASSWORD        = '' # Obvious security flaw if you fill this in.
DEFAULT_CHECK_INTERVAL  = 10 # Minutes
REDDIT_INBOX_USER_URL   = 'http://www.reddit.com/message/inbox'


class Application(object):
    
    config_dialog = None
    tooltip = None
    tray_icon = None
    menu = None
    reddit = None
    worker = None
    
    interval = None
    username = None
    password = None
    notify = None
    mail = None
    karma = None
    comment_karma = None
    messages = None
    checking = False
    
    def __init__(self):
        self.reddit = reddit.Reddit()
        self.config_dialog = ConfigDialog(self)
    
    def quit(self, widget):
        gtk.main_quit()
        sys.exit(0)
    
    def update(self, widget):
        return
    
    def clear_messages(self, widget):
        self.messages = []
    
    def go_to_inbox(self, widget):
        return


class ConfigDialog(object):
    
    app = None
    widgets = None
    
    def __init__(self, parent):
        self.app = parent
        
        self.widgets = gtk.Builder()
        self.widgets.add_from_file(UI_DEFINITION)
        
        signals = {
            'on_cancel_button_activate' : self.cancel,
            'on_ok_button_activate'     : self.ok,
            'on_entry_changed'          : self.entry_contents_changed,
        }
        self.widgets.connect_signals(signals)
        
        self.widgets.get_object('message_label').set_line_wrap(True)
        self.widgets.get_object('message_frame').hide()
        
        if not pynotify:
            self.widgets.get_object('notify_checkbutton').set_active(False)
            self.widgets.get_object('notify_checkbutton').hide()
        else:
            self.widgets.get_object('notify_checkbutton').set_active(True)
        
        if DEFAULT_USERNAME:
            self.widgets.get_object('username_entry').set_text(DEFAULT_USERNAME)
        if DEFAULT_PASSWORD:
            self.widgets.get_object('password_entry').set_text(DEFAULT_PASSWORD)
        
        if not DEFAULT_USERNAME and not DEFAULT_PASSWORD:
            self.widgets.get_object('ok_button').set_sensitive(False)
        
        if DEFAULT_CHECK_INTERVAL:
            self.widgets.get_object('update_spinbutton').set_value(DEFAULT_CHECK_INTERVAL)
        else:
            self.widgets.get_object('update_spinbutton').set_value(10)
        
        self.widgets.get_object('username_entry').set_activates_default(True)
        self.widgets.get_object('password_entry').set_activates_default(True)
        self.widgets.get_object('update_spinbutton').set_activates_default(True)
        
        self.widgets.get_object('window').set_default(self.widgets.get_object('ok_button'))
        self.widgets.get_object('window').show()
    
    def set_sensitive(self, bool):
        self.widgets.get_object('username_entry').set_sensitive(bool)
        self.widgets.get_object('password_entry').set_sensitive(bool)
        self.widgets.get_object('notify_checkbutton').set_sensitive(bool)
        self.widgets.get_object('update_spinbutton').set_sensitive(bool)
        self.widgets.get_object('ok_button').set_sensitive(bool)
    
    def entry_contents_changed(self, widget):
        if not len(self.widgets.get_object('username_entry').get_text()) >= 3 or not len(self.widgets.get_object('password_entry').get_text()) >= 3:
            self.widgets.get_object('ok_button').set_sensitive(False)
        else:
            self.widgets.get_object('ok_button').set_sensitive(True)
    
    def cancel(self, widget, event=None):
        gtk.main_quit()
        sys.exit(0)
    
    def ok(self, widget):
        if not self.app.checking:
            self.app.checking = True
            
            self.set_sensitive(False)
            
            self.widgets.get_object('message_frame').show()
            self.widgets.get_object('message_label').set_text('Logging in to reddit...')
            
            self.app.notify = self.widgets.get_object('notify_checkbutton').get_active()
            self.app.interval = self.widgets.get_object('update_spinbutton').get_value()
            
            def login(username, password):
                 # This is run in a new thread to avoid blocking the UI if
                 # connecting to reddit takes a little while.
                
                try:
                    self.app.reddit.login(username, password)
                    self.widgets.get_object('message_label').set_text('Fetching karma scores...')
                    self.app.karma, self.app.comment_karma = self.app.reddit.get_karma()
                    self.widgets.get_object('message_label').set_text('Checking for new messages...')
                    self.app.messages = self.app.reddit.get_new_mail()
                    self.app.username = username
                    self.app.password = password
                    self.widgets.get_object('message_label').set_markup('Logged in to reddit as <i>%s</i>.' % self.app.username)
                    
                    self.app.tray_icon = TrayIcon(self.app)
                    self.widgets.get_object('window').hide()
                except reddit.RedditInvalidUsernamePasswordException:
                    self.widgets.get_object('message_label').set_text('Log in failed. Please ensure that your username and password are correct.')
                    self.set_sensitive(True)
                    self.widgets.get_object('username_entry').grab_focus()
                finally:
                    self.app.checking = False

            self.app.worker = threading.Thread(target=login, args=(self.widgets.get_object('username_entry').get_text(), self.widgets.get_object('password_entry').get_text()))
            self.app.worker.start()


def TrayIcon(app):
    if egg.trayicon:
        return EggTrayIcon(app)
    else:
        return GtkTrayIcon(app)


class EggTrayIcon(egg.trayicon.TrayIcon):
    
    app = None
    icon = None
    menu = None
    
    def __init__(self, parent):
        egg.trayicon.TrayIcon.__init__(self, 'Reddit Monitor')
        
        self.app = parent
        self.menu = PopupMenu(parent)
        
        self.icon = gtk.image_new_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(REDDIT_ICON, 24, 24))
        
        event_box = gtk.EventBox()
        event_box.add(self.icon)
        event_box.connect('button-press-event', self.button_pressed)
        
        self.icon.set_has_tooltip(True)
        self.icon.connect('query-tooltip', self.show_tooltip)
        
        self.add(event_box)
        self.show_all()
    
    def show_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        tooltip.set_custom(TooltipWidget(self.app))
        return True
    
    def button_pressed(self, widget, event):
        if event.button == 3:
            self.menu.popup(widget, event.button, event.time)
    
    def set_icon(self, path):
        self.icon = gtk.image_new_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(path, 24, 24))


class GtkTrayIcon(gtk.StatusIcon):
    
    app = None
    menu = None
    
    def __init__(self, parent):
        gtk.StatusIcon.__init__(self)
        
        self.app = parent
        self.menu = PopupMenu(parent)
        
        self.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(REDDIT_ICON))
        
        self.connect('popup-menu', self.menu.popup)
        
        if self.app.messages:
            if len(self.app.messages) == 1:
                messages_string = 'New messages: 1'
            else:
                messages_string = 'New messages: %d' % len(self.app.messages)
        else:
            messages_string = 'New messages: 0'
        
        tooltip_string = '%s\nKarma: %d\nComment karma: %d\n%s' % (self.app.username, self.app.karma, self.app.comment_karma, messages_string)
        self.set_tooltip(tooltip_string)
        
        self.set_visible(True)
    
    def set_icon(self, path):
        self.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(path))


class PopupMenu(object):
    
    app = None
    ui_manager = None
    action_group = None
    
    def __init__(self, parent):
        self.app = parent
        
        actions = [
            ('Inbox', gtk.STOCK_HOME, 'Go to inbox', None, None, self.app.go_to_inbox),
            ('Refresh', gtk.STOCK_REFRESH, 'Check for new messages', None, None, self.app.update),
            ('Reset', gtk.STOCK_CLEAR, 'Clear new messages', None, None, self.app.clear_messages),
            ('Quit', gtk.STOCK_QUIT, None, None, None, self.app.quit)
        ]
        
        self.action_group = gtk.ActionGroup('Reddit Monitor')
        self.action_group.add_actions(actions)
        
        ui = """
            <ui>
                <popup name='TrayMenu'>
                    <menuitem action='Inbox' />
                    <separator/>
                    <menuitem action='Refresh' />
                    <menuitem action='Reset' />
                    <separator/>
                    <menuitem action='Quit' />
                </popup>
            </ui>
        """
        
        self.ui_manager = gtk.UIManager()
        self.ui_manager.insert_action_group(self.action_group, 0)
        self.ui_manager.add_ui_from_string(ui)
    
    def popup(self, widget, button, activate_time, data=None):
        self.ui_manager.get_widget("/TrayMenu").popup(None, None, None, button, activate_time)


class TooltipWidget(gtk.HBox):
    
    app = None
    
    def __init__(self, parent):
        gtk.HBox.__init__(self)
        
        self.app = parent
        
        icon = gtk.image_new_from_file(REDDIT_ICON)
        karma_label = gtk.Label()
        comment_karma_label = gtk.Label()
        messages_label = gtk.Label()
        user_label = gtk.Label()
        
        karma_label.set_alignment(0, 0.5)
        comment_karma_label.set_alignment(0, 0.5)
        messages_label.set_alignment(0, 0.5)
        
        user_label.set_markup('<b><big>%s</big></b>' % self.app.username)
        
        karma_label.set_markup('Karma: <b>%d</b>' % self.app.karma)
        comment_karma_label.set_markup('Comment karma: <b>%d</b>' % self.app.comment_karma)
        
        if self.app.messages:
            self.messages_label.show()
            if len(self.app.messages) == 1:
                messages_label.set_markup('New messages: <b>1</b>')
            else:
                messages_label.set_markup('New messages: <b>%d</b>' % len(self.app.messages))
        else:
            messages_label.set_markup('New messages: <b>0</b>')
        
        vbox = gtk.VBox()
        vbox.set_spacing(4)
        vbox.pack_start(user_label)
        vbox.pack_start(karma_label)
        vbox.pack_start(comment_karma_label)
        vbox.pack_start(messages_label)
        
        self.pack_start(icon)
        self.pack_start(vbox)
        self.set_spacing(6)
        self.show_all()


def main(args):
    if gtk.check_version(2, 12, 0):
        # This will return None if you have GTK+ version 2.12 or higher. It will
        # return a less useful error string than the one we're going to display
        # below otherwise.
        print 'Reddit Monitor requires GTK+ (and it\'s Python bindings) version 2.12 or higher.'
        sys.exit(0)
    
    gtk.gdk.threads_init()
    
    app = Application()
    gtk.main()


if __name__ == '__main__':
    main(sys.argv)

