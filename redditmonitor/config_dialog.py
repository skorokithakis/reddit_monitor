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


class ConfigDialog(object):
    
    app = None
    widgets = None
    sound_chooser = None
    
    def __init__(self, parent, username=None, password=None):
        self.app = parent
        
        self.widgets = gtk.Builder()
        self.widgets.add_from_file(self.app.resources['ui_definition'])
        
        self.widgets.get_object('message_label').set_line_wrap(True)
        self.widgets.get_object('message_frame').hide()
        
        self.widgets.get_object('image').set_from_file(self.app.resources['reddit_icon'])
        
        if not self.app.modules['pynotify']:
            self.widgets.get_object('notify_checkbutton').set_active(False)
            self.widgets.get_object('notify_checkbutton').hide()
        
        if not self.app.modules['gnomekeyring']:
            self.widgets.get_object('remember_checkbutton').set_active(False)
            self.widgets.get_object('remember_checkbutton').hide()
            self.widgets.get_object('auto_checkbutton').set_active(False)
            self.widgets.get_object('auto_checkbutton').hide()
        
        if username and password:
            self.widgets.get_object('username_entry').set_text(username)
            self.widgets.get_object('password_entry').set_text(password)
            self.widgets.get_object('ok_button').grab_focus()
        else:
            self.widgets.get_object('username_entry').grab_focus()
            self.widgets.get_object('ok_button').set_sensitive(False)
        
        if self.app.config:
            self.widgets.get_object('update_spinbutton').set_value(self.app.options['interval'] / 60000)
            self.widgets.get_object('notify_checkbutton').set_active(self.app.options['notify'])
            self.widgets.get_object('remember_checkbutton').set_active(self.app.options['remember_username_password'])
            self.widgets.get_object('sound_checkbutton').set_active(self.app.options['sound'])
            self.widgets.get_object('auto_checkbutton').set_active(self.app.options['login_automatically'])
        else:
            # Default values:
            if self.app.modules['gnomekeyring']:
                self.widgets.get_object('remember_checkbutton').set_active(True)
            
            if self.app.modules['pynotify']:
                self.widgets.get_object('notify_checkbutton').set_active(True)
        
        if self.app.resources['sound_file']:
            self.sound_chooser = SoundChooserButton(file=self.app.resources['sound_file'])
        else:
            self.sound_chooser = SoundChooserButton()
        
        self.widgets.get_object('pack_filechooserbutton_here').pack_start(self.sound_chooser)
        self.widgets.get_object('pack_filechooserbutton_here').show_all()
        
        self.widgets.get_object('username_entry').set_activates_default(True)
        self.widgets.get_object('password_entry').set_activates_default(True)
        self.widgets.get_object('update_spinbutton').set_activates_default(True)
        
        self.widgets.get_object('window').set_default(self.widgets.get_object('ok_button'))
        self.widgets.get_object('window').show()
        
        signals = {
            'on_cancel_button_activate'         : self.cancel,
            'on_ok_button_activate'             : self.ok,
            'on_entry_changed'                  : self.entry_contents_changed,
            'on_remember_checkbutton_toggled'   : self.remember_toggled,
            'on_sound_checkbutton_toggled'      : self.sound_toggled,
        }
        self.widgets.connect_signals(signals)
        
        if username and password and self.app.options['login_automatically']:
            self.widgets.get_object('ok_button').clicked()
    
    def set_sensitive(self, bool):
        self.widgets.get_object('username_entry').set_sensitive(bool)
        self.widgets.get_object('password_entry').set_sensitive(bool)
        self.widgets.get_object('remember_checkbutton').set_sensitive(bool)
        self.widgets.get_object('auto_checkbutton').set_sensitive(bool)
        self.widgets.get_object('notify_checkbutton').set_sensitive(bool)
        self.widgets.get_object('sound_checkbutton').set_sensitive(bool)
        self.widgets.get_object('update_spinbutton').set_sensitive(bool)
        self.widgets.get_object('ok_button').set_sensitive(bool)
        self.widgets.get_object('label3').set_sensitive(bool)
        self.widgets.get_object('label4').set_sensitive(bool)
        self.sound_chooser.set_sensitive(bool)
        self.widgets.get_object('label6').set_sensitive(bool)
    
    def remember_toggled(self, widget):
        if widget.get_active():
            self.widgets.get_object('auto_checkbutton').set_sensitive(True)
        else:
            self.widgets.get_object('auto_checkbutton').set_sensitive(False)
            self.widgets.get_object('auto_checkbutton').set_active(False)
    
    def sound_toggled(self, widget):
        if widget.get_active():
            self.sound_chooser.set_sensitive(True)
            self.widgets.get_object('label6').set_sensitive(True)
        else:
            self.sound_chooser.set_sensitive(False)
            self.widgets.get_object('label6').set_sensitive(False)
    
    def entry_contents_changed(self, widget):
        if not len(self.widgets.get_object('username_entry').get_text()) >= 3 or not len(self.widgets.get_object('password_entry').get_text()) >= 3:
            self.widgets.get_object('ok_button').set_sensitive(False)
        else:
            self.widgets.get_object('ok_button').set_sensitive(True)
    
    def cancel(self, widget, event=None):
        self.app.quit(widget)
    
    def ok(self, widget):
        if not self.app.checking:
            self.app.checking = True
            
            self.set_sensitive(False)
            
            self.widgets.get_object('message_frame').show()
            self.widgets.get_object('message_label').set_text('Logging in to reddit...')
            
            self.app.options['remember_username_password'] = self.widgets.get_object('remember_checkbutton').get_active()
            self.app.options['login_automatically'] = self.widgets.get_object('auto_checkbutton').get_active()
            self.app.options['notify'] = self.widgets.get_object('notify_checkbutton').get_active()
            self.app.options['sound'] = self.widgets.get_object('sound_checkbutton').get_active()
            self.app.options['interval'] = int(self.widgets.get_object('update_spinbutton').get_value()) * 60000
            
            self.app.login(self.widgets.get_object('username_entry').get_text(), self.widgets.get_object('password_entry').get_text())
