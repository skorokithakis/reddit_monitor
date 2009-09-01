import gtk, egg


# I really hate all of this and would love to delete it. GTK+ actually has the
# code to do this properly now as of 2.16, but the Python bindings haven't been 
# updated yet. T_T


class TooltipWidget(gtk.HBox):
    
    app = None
    
    def __init__(self, parent, icon):
        gtk.HBox.__init__(self)
        
        self.app = parent
        
        icon = gtk.image_new_from_file(icon)
        karma_label = gtk.Label()
        comment_karma_label = gtk.Label()
        messages_label = gtk.Label()
        user_label = gtk.Label()
        
        user_label.set_alignment(0, 0.5)
        karma_label.set_alignment(0, 0.5)
        comment_karma_label.set_alignment(0, 0.5)
        messages_label.set_alignment(0, 0.5)
        
        user_label.set_markup('<b><big>%s</big></b>' % self.app.username)
        
        karma_label.set_markup('Karma: <b>%d</b>' % self.app.karma)
        comment_karma_label.set_markup('Comment karma: <b>%d</b>' % self.app.comment_karma)
        
        if self.app.messages:
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


class EggTrayIcon(egg.trayicon.TrayIcon):
    
    app = None
    icon = None
    menu = None
    reddit_icon = None
    
    def __init__(self, parent, menu, reddit_icon, mail_icon):
        egg.trayicon.TrayIcon.__init__(self, 'Reddit Monitor')
        
        self.app = parent
        self.menu = menu
        self.reddit_icon = reddit_icon
        
        if self.app.messages:
            self.icon = gtk.image_new_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(mail_icon, 24, 24))
            self.menu.ui_manager.get_widget('/TrayMenu/Reset').set_sensitive(True)
        else:
            self.icon = gtk.image_new_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(reddit_icon, 24, 24))
            self.menu.ui_manager.get_widget('/TrayMenu/Reset').set_sensitive(False)
        
        event_box = gtk.EventBox()
        event_box.add(self.icon)
        event_box.connect('button-press-event', self.button_pressed)
        
        self.icon.set_has_tooltip(True)
        self.icon.connect('query-tooltip', self.show_tooltip)
        
        self.add(event_box)
        self.show_all()
    
    def show_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        tooltip.set_custom(TooltipWidget(self.app, self.reddit_icon))
        return True
    
    def button_pressed(self, widget, event):
        if event.button == 3:
            self.menu.popup(widget, event.button, event.time)
    
    def set_icon(self, path):
        self.icon.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(path, 24, 24))
