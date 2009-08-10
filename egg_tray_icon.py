import gtk, egg

class EggTrayIcon(egg.trayicon.TrayIcon):
    
    app = None
    icon = None
    menu = None
    
    def __init__(self, parent):
        egg.trayicon.TrayIcon.__init__(self, 'Reddit Monitor')
        
        self.app = parent
        self.menu = PopupMenu(parent)
        
        if self.app.messages:
            self.icon = gtk.image_new_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(NEW_MAIL_ICON, 24, 24))
        else:
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
        self.icon.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file_at_size(path, 24, 24))
