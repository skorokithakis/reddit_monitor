#!/usr/bin/env python
#-*- coding:utf-8 -*-

import sys
import os
import time
import subprocess
import threading

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
        
        self.app.config_dialog = self.widgets.get_object('window')
        self.app.config_dialog.set_default(self.widgets.get_object('ok_button'))
        self.app.config_dialog.show()
    
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
                    self.app.username = username
                    self.app.password = password
                    self.widgets.get_object('message_label').set_markup('You are now logged in to reddit as <i>%s</i>.' % self.app.username)
                    
                    self.app.tray_icon = TrayIcon(self.app)
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
    
    def __init__(self, parent):
        egg.trayicon.TrayIcon.__init__(self, 'Reddit Monitor')
        
        self.app = parent
        self.icon = gtk.image_new_from_file(os.path.abspath(REDDIT_ICON))
        
        event_box = gtk.EventBox()
        event_box.add(self.icon)
        
        self.add(event_box)
        self.show_all()


class GtkTrayIcon(gtk.StatusIcon):
    
    app = None
    icon = None
    
    def __init__(self, parent):
        gtk.StatusIcon.__init__(self)
        
        self.app = parent
        self.icon = gtk.image_new_from_file(os.path.abspath(REDDIT_ICON))
        
        self.set_from_pixbuf(self.icon)
        
        self.show()


class TooltipWidget(gtk.HBox):
    
    app = None
    
    def __init__(self, parent):
        gtk.HBox.__init__(self)
        
        self.app = parent
        
        self.icon = gtk.image_new_from_file(os.path.abspath(REDDIT_ICON))
        self.karma_label = gtk.Label()
        self.comment_karma_label = gtk.Label()
        self.messages_label = gtk.Label()
        self.user_label = gtk.Label()
        
        self.user_label.set_markup('<b><big>%s</big></b>' % user)
        
        if self.app.messages:
            self.messages_label.show()
            if len(msgs) == 1:
                self.messages_label.set_markup('You have <b>1</b> new message!')
            else:
                self.messages_label.set_markup('You have <b>%d</b> new messages!' % len(msgs))
        else:
            self.messages_label.hide()
        
        karma, comment_karma = reddit.get_karma()
        
        self.karma_label.set_markup('Karma: <b>%d</b>' % karma)
        self.karma_label.set_markup('Comment karma: <b>%d</b>' % comment_karma)
        
        vbox = gtk.VBox()
        vbox.set_spacing(6)
        vbox.pack_start(self.user_label)
        vbox.pack_start(self.messages_label)
        vbox.pack_start(self.karma_label)
        vbox.pack_start(self.comment_karma_label)
        
        self.pack-start(self.icon)
        self.pack_start(vbox)
        self.set_spacing(6)
        self.show()


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

