import gtk


class SoundChooserButton(gtk.FileChooserButton):
    
    def __init__(self, file=None):
        # FIXME: There's a bug here that I just can't get to the bottom of. It
        #        could be in the GTK+ bindings themselves. If this is called
        #        with a file, then the file filter will not be selected. Not a
        #        huge deal but still annoying.
        
        gtk.FileChooserButton.__init__(self, title='Select Sound File')
        
        filter = gtk.FileFilter()
        filter.set_name('All files')
        filter.add_pattern('*')
        self.add_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name('Sound Files (*.wav)')
        filter.add_pattern('*.wav')
        self.add_filter(filter)
        self.set_filter(filter)
        
        if file:
            self.set_filename(file)


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
