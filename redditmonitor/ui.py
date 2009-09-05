import gtk

from config_dialog import ConfigDialog


def TrayIcon(app):
    if app.modules['egg']:
        from egg_tray_icon import EggTrayIcon
        return EggTrayIcon(app, PopupMenu(app))
    else:
        return GtkTrayIcon(app)
    
    if app.messages:
        app.play_sound()
        app.show_notification()


class GtkTrayIcon(gtk.StatusIcon):
    
    app = None
    menu = None
    
    def __init__(self, parent):
        gtk.StatusIcon.__init__(self)
        
        self.app = parent
        self.menu = PopupMenu(parent)
        
        self.connect('popup-menu', self.menu.popup)
        
        if self.app.messages:
            self.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(self.app.resources['new_mail_icon']))
            self.menu.ui_manager.get_widget('/TrayMenu/Reset').set_sensitive(True)
            
            if len(self.app.messages) == 1:
                messages_string = 'New messages: 1'
            else:
                messages_string = 'New messages: %d' % len(self.app.messages)
        else:
            self.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(self.app.resources['reddit_icon']))
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
    
    def __init__(self, parent):
        self.app = parent
        
        actions = [
            ('Inbox', gtk.STOCK_HOME, 'Go to _inbox', None, None, self.app.go_to_inbox),
            ('Refresh', gtk.STOCK_REFRESH, '_Check for messages', None, None, self.app.update),
            ('Reset', gtk.STOCK_CLEAR, 'Mark as _read', None, None, self.app.clear_messages),
            ('Quit', gtk.STOCK_QUIT, None, None, None, self.app.quit)
        ]
        
        toggle_actions = [
            ('Notify', None, '_Show notifications', None, None, self.app.toggle_notify),
            ('Sound', None, '_Play sounds', None, None, self.app.toggle_sound),
        ]
        
        action_group = gtk.ActionGroup('Reddit Monitor')
        action_group.add_actions(actions)
        action_group.add_toggle_actions(toggle_actions)
        
        ui = """
            <ui>
                <popup name='TrayMenu'>
                    <menuitem action='Inbox' />
                    <separator />
                    <menuitem action='Refresh' />
                    <menuitem action='Reset' />
                    <separator />
                    <menuitem action='Notify' />
                    <menuitem action='Sound' />
                    <separator />
                    <menuitem action='Quit' />
                </popup>
            </ui>
        """
        
        self.ui_manager = gtk.UIManager()
        self.ui_manager.insert_action_group(action_group, 0)
        self.ui_manager.add_ui_from_string(ui)
        
        self.ui_manager.get_widget('/TrayMenu/Notify').set_active(self.app.options['notify'])
        self.ui_manager.get_widget('/TrayMenu/Sound').set_active(self.app.options['sound'])
        
        if not self.app.modules['pynotify']:
            self.ui_manager.get_widget('/TrayMenu/Notify').set_visible(False)
        
        if not self.app.modules['gnome']:
            self.ui_manager.get_widget('/TrayMenu/Sound').set_visible(False)
    
    def popup(self, widget, button, activate_time, data=None):
        self.ui_manager.get_widget('/TrayMenu').popup(None, None, None, button, activate_time)
