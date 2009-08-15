#!/usr/bin/env python

import sys
import os
import time
import subprocess
import threading
import webbrowser
import ConfigParser

import gtk

try:
    import glib
    TIMEOUT_ADD = glib.timeout_add
    IDLE_ADD = glib.idle_add
except ImportError:
    import gobject
    TIMEOUT_ADD = gobject.timeout_add
    IDLE_ADD = gobject.idle_add

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
    egg = None

import reddit


UI_DEFINITION           = os.path.abspath('reddit_tray_icon.ui')
REDDIT_ICON             = os.path.abspath('icons/reddit_trans.png')
NEW_MAIL_ICON           = os.path.abspath('icons/new_mail_trans.png')
BUSY_ICON               = os.path.abspath('icons/busy.gif')
DEFAULT_CHECK_INTERVAL  = 10 # Minutes
REDDIT_INBOX_USER_URL   = 'http://www.reddit.com/message/inbox'

# This will be set to True when the program is run, if xdg-open is found
# somewhere in the path.
XDG_OPEN                = False


class Application(object):
    
    config_dialog = None
    tooltip = None
    tray_icon = None
    menu = None
    reddit = None
    worker = None
    timer = None
    notification = None
    
    config = None
    interval = None
    username = None
    notify = None
    mail = None
    karma = None
    comment_karma = None
    messages = None
    checking = False
    logged_in = False
    
    def __init__(self):
        self.config = self.load_config()
        self.reddit = reddit.Reddit()
        self.config_dialog = ConfigDialog(self)
    
    def load_config(self):
        config_file = os.path.expanduser('~/.config/reddit_monitor')
        
        if not os.path.exists(config_file):
            return None
        else:
            parser = ConfigParser.SafeConfigParser()
            parser.read([config_file])
            return parser
    
    def save_config(self):
        config_file = os.path.expanduser('~/.config/reddit_monitor')
        
        if os.path.exists(config_file):
            os.remove(config_file)
        
        parser = ConfigParser.SafeConfigParser()
        parser.add_section('Reddit')
        parser.set('Reddit', 'username', self.username)
        parser.set('Reddit', 'interval', str(self.interval))
        parser.set('Reddit', 'notify', str(self.notify))
        parser.write(open(config_file, 'w'))
        
    
    def quit(self, widget):
        self.save_config()
        gtk.main_quit()
        sys.exit(0)
    
    def update(self, widget=None):
        if not self.checking:
            self.checking = True
            
            self.tray_icon.set_icon(BUSY_ICON)
            
            def check():
                # This is run in a new thread to avoid blocking the UI if
                # connecting to reddit takes a little while.
                
                self.karma, self.comment_karma = self.reddit.get_karma()
                self.messages = self.reddit.get_new_mail()
                if self.messages:
                    self.tray_icon.set_icon(NEW_MAIL_ICON)
                    self.show_notification()
                else:
                    self.tray_icon.set_icon(REDDIT_ICON)
                
                self.checking = False

            self.worker = threading.Thread(target=check)
            self.worker.start()
        
        return True
    
    def clear_messages(self, widget=None):
        self.messages = []
        self.tray_icon.set_icon(REDDIT_ICON)
    
    def go_to_inbox(self, widget):
        open_url(REDDIT_INBOX_USER_URL)
    
    def show_notification(self):
        if self.messages and self.notify:
            latest_message = self.messages[len(self.messages) - 1]
            
            notification_body = 'from <b>%s</b>\n\n%s' % (latest_message['author'], latest_message['body'])
            self.notification = pynotify.Notification(latest_message['subject'], notification_body)
            self.notification.add_action('home', 'Inbox', self.inbox_clicked)
            self.notification.set_icon_from_pixbuf(gtk.gdk.pixbuf_new_from_file(REDDIT_ICON))
            
            if latest_message['was_comment']:
                self.notification.add_action('context', 'Context', self.context_clicked, latest_message['context'])
            
            self.notification.show()
    
    def inbox_clicked(self, n, action):
        open_url(REDDIT_INBOX_USER_URL)
        self.clear_messages()
    
    def context_clicked(self, n, action, context):
        open_url('http://www.reddit.com' + context)
        self.clear_messages()


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
        
        if self.app.config:
            self.widgets.get_object('username_entry').set_text(self.app.config.get('Reddit', 'username'))
            self.widgets.get_object('update_spinbutton').set_value(self.app.config.getint('Reddit', 'interval') / 60000)
            self.widgets.get_object('notify_checkbutton').set_active(self.app.config.getboolean('Reddit', 'notify'))
            self.widgets.get_object('password_entry').grab_focus()
        else:
            # Default values:
            self.widgets.get_object('update_spinbutton').set_value(10)
            self.widgets.get_object('notify_checkbutton').set_active(True)
        
        self.widgets.get_object('ok_button').set_sensitive(False)
        
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
            self.app.interval = int(self.widgets.get_object('update_spinbutton').get_value()) * 60000
            
            def check_done():
                if self.app.logged_in:
                    self.app.tray_icon = TrayIcon(self.app)
                    self.widgets.get_object('window').hide()
                    self.app.timer = TIMEOUT_ADD(self.app.interval, self.app.update)
                    return False
                else:
                    return True
            
            IDLE_ADD(check_done)
            
            def login(username, password):
                # This is run in a new thread to avoid blocking the UI if
                # connecting to reddit takes a little while.
                
                self.app.logged_in = False
                
                try:
                    self.app.reddit.login(username, password)
                    self.widgets.get_object('message_label').set_text('Fetching karma scores...')
                    self.app.karma, self.app.comment_karma = self.app.reddit.get_karma()
                    self.widgets.get_object('message_label').set_text('Checking for new messages...')
                    self.app.messages = self.app.reddit.get_new_mail()
                    self.app.username = username
                    self.widgets.get_object('message_label').set_markup('Logged in to reddit as <i>%s</i>.' % self.app.username)
                    
                    self.app.logged_in = True
                except reddit.RedditInvalidUsernamePasswordException:
                    self.widgets.get_object('message_label').set_text('Log in failed. Please ensure that your username and password are correct.')
                    self.set_sensitive(True)
                    self.widgets.get_object('username_entry').grab_focus()
                    
                    self.app.logged_in = False
                finally:
                    self.app.checking = False
                    
            self.app.worker = threading.Thread(target=login, args=(self.widgets.get_object('username_entry').get_text(), self.widgets.get_object('password_entry').get_text()))
            self.app.worker.start()


def TrayIcon(app):
    app.show_notification()
    
    if egg:
        from egg_tray_icon import EggTrayIcon
        return EggTrayIcon(app)
    else:
        return GtkTrayIcon(app)


class GtkTrayIcon(gtk.StatusIcon):
    
    app = None
    menu = None
    
    def __init__(self, parent):
        gtk.StatusIcon.__init__(self)
        
        self.app = parent
        self.menu = PopupMenu(parent)
        
        self.connect('popup-menu', self.menu.popup)
        
        if self.app.messages:
            self.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(NEW_MAIL_ICON))
            self.menu.ui_manager.get_widget('/TrayMenu/Reset').set_sensitive(True)
            
            if len(self.app.messages) == 1:
                messages_string = 'New messages: 1'
            else:
                messages_string = 'New messages: %d' % len(self.app.messages)
        else:
            self.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(REDDIT_ICON))
            self.menu.ui_manager.get_widget('/TrayMenu/Reset').set_sensitive(False)
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
            ('Refresh', gtk.STOCK_REFRESH, 'Check for messages', None, None, self.app.update),
            ('Reset', gtk.STOCK_CLEAR, 'Mark as read', None, None, self.app.clear_messages),
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
        self.ui_manager.get_widget('/TrayMenu').popup(None, None, None, button, activate_time)


def open_url(url):
    if XDG_OPEN:
        subprocess.call(['xdg-open', url])
    else:
        webbrowser.open(url)


def main(args):
    if gtk.check_version(2, 12, 0):
        # This will return None if you have GTK+ version 2.12 or higher. It will
        # return a less useful error string than the one we're going to display
        # below otherwise.
        print 'Reddit Monitor requires GTK+ (and it\'s Python bindings) version 2.12 or higher.'
        sys.exit(0)
    
    # Check to see if we have xdg-open.
    for path in os.environ.get('PATH').split(':'):
        if os.path.exists(os.path.join(path, 'xdg-open')):
            XDG_OPEN = True
    
    if pynotify:
        pynotify.init('Reddit Monitor')
    
    gtk.gdk.threads_init()
    
    app = Application()
    gtk.main()


if __name__ == '__main__':
    main(sys.argv)
