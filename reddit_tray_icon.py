#!/usr/bin/env python
import pygtk
pygtk.require('2.0')
import os
import gtk
import gobject
import sys
import time
import subprocess

import reddit

try:
	import pynotify
	if not pynotify.init('Reddit'):
		pynotify = False
except ImportError:
	pynotify = False

if not pynotify:
	print 'Notice: pynotify could not be loaded. Balloon notifications will be unavailable.'

REDDIT_ICON            = 'icons/reddit.png'
NEW_MAIL_ICON          = 'icons/new_mail.png'
BUSY_ICON              = 'icons/busy.gif'
DEFAULT_USERNAME       = ''
DEFAULT_PASSWORD       = '' #obvious security flaw if you fill this in.
DEFAULT_CHECK_INTERVAL = 10 #minutes

class RedditConfigWindow(gtk.Window):

	user = None
	passwd = None
	interval = None

	def __init__(self):
		gtk.Window.__init__(self)
		self.set_title('Reddit Tray Icon Preferences')
		self.set_position(gtk.WIN_POS_CENTER)
		self.set_modal(True)
		self.set_resizable(False)
		self.set_icon_from_file(os.path.abspath(REDDIT_ICON))
		
		vbox = gtk.VBox(homogeneous=False, spacing=6)
		vbox.set_border_width(6)

		table = gtk.Table(rows=4, columns=2, homogeneous=False)
		table.set_row_spacings(6)
		table.set_col_spacings(6)

		label_username = gtk.Label('Username:')
		label_username.set_alignment(1, 0.5)
		table.attach(label_username, 0, 1, 0, 1)

		self.text_username = gtk.Entry(max=0)
		self.text_username.set_text(DEFAULT_USERNAME)
		table.attach(self.text_username, 1, 2, 0, 1)

		label_password = gtk.Label('Password:')
		label_password.set_alignment(1, 0.5)
		table.attach(label_password, 0, 1, 1, 2)
		
		self.text_password = gtk.Entry(max=0)
		self.text_password.set_text(DEFAULT_PASSWORD)
		self.text_password.set_visibility(False)
		self.text_password.set_invisible_char('*')
		table.attach(self.text_password, 1, 2, 1, 2)

		label_interval = gtk.Label('Interval (minutes):')
		label_interval.set_alignment(1, 0.5)
		table.attach(label_interval, 0, 1, 2, 3)

		self.text_interval = gtk.Entry(max=0)
		self.text_interval.set_text(str(DEFAULT_CHECK_INTERVAL))
		table.attach(self.text_interval, 1, 2, 2, 3)
		
		vbox.pack_start(table)
		
		if pynotify:
			self.check_notify = gtk.CheckButton(label='Show notifications')
			self.check_notify.set_active(True)
			vbox.pack_start(self.check_notify)

		bbox = gtk.HButtonBox()
		bbox.set_layout(gtk.BUTTONBOX_END)
		bbox.set_spacing(8)
		
		ok_btn = gtk.Button(stock=gtk.STOCK_OK)
		ok_btn.connect("clicked", self.on_ok)
		ok_btn.set_flags(gtk.CAN_DEFAULT)

		close_btn = gtk.Button(stock=gtk.STOCK_CANCEL)
		close_btn.connect("clicked", self.on_cancel)
		
		bbox.add(close_btn)
		bbox.add(ok_btn)
		vbox.pack_start(bbox)
		self.add(vbox)

		self.set_default(ok_btn)
		self.show_all()
		gtk.main()

	def on_ok(self, widget, callback_data=None):
		global SHOW_NOTIFICATIONS 
		SHOW_NOTIFICATIONS = self.check_notify.get_active()
		self.hide()
		gtk.main_quit()

	def get_username(self):
		return self.text_username.get_text()

	def get_password(self):
		return self.text_password.get_text()

	def get_interval(self):
		return self.text_interval.get_text()

	def on_cancel(self, widget, callback_data=None):
		gtk.main_quit()
		sys.exit(0)


class RedditTrayIcon():

	checking = False
	newmsgs = []

	def __init__(self, user, password, interval):

		self.reddit = reddit.Reddit()
		self.reddit.login(user, password)
		self.interval = interval

		#create the tray icon
		self.tray_icon = gtk.StatusIcon()
		self.tray_icon.connect('activate', self.on_check_now)
		self.tray_icon.connect('popup-menu', self.on_tray_icon_click)

		#load the three icons
		self.reddit_icon = gtk.gdk.pixbuf_new_from_file_at_size(os.path.abspath(REDDIT_ICON), 24, 24)
		self.new_mail_icon = gtk.gdk.pixbuf_new_from_file_at_size(os.path.abspath(NEW_MAIL_ICON), 24, 24)
		self.busy_icon = gtk.gdk.pixbuf_new_from_file_at_size(os.path.abspath(BUSY_ICON), 24, 24)

		self.tray_icon.set_from_pixbuf(self.reddit_icon)

		#create the popup menu
		inbox_now = gtk.MenuItem('_Inbox', True)
		inbox_now.connect('activate', self.on_inbox)
		
		check_now = gtk.MenuItem('_Check Now', True)
		check_now.connect('activate', self.on_check_now)

		reset_now = gtk.MenuItem('_Reset Icon', True)
		reset_now.connect('activate', self.on_reset)

		quit = gtk.MenuItem('_Quit', True)
		quit.connect('activate', self.on_quit)
		
		self.menu = gtk.Menu()
		self.menu.append(inbox_now)
		self.menu.append(check_now)
		self.menu.append(reset_now)
		self.menu.append(quit)
		self.menu.show_all()

		while gtk.events_pending():
			gtk.main_iteration(True)

		self.timer = gobject.timeout_add(self.interval, self.on_check_now)

	def on_tray_icon_click(self, status_icon, button, activate_time):
		self.menu.popup(None, None, None, button, activate_time)
	
	def on_inbox(self, event=None):
		open_url('http://www.reddit.com/message/inbox')

	def on_reset(self, event=None):
		self.newmsgs = []
		self.tray_icon.set_from_pixbuf(self.reddit_icon)

	def on_quit(self, event=None):
		gtk.main_quit()
		sys.exit(0)

	def on_check_now(self, event=None):

		#poor mans lock
		if self.checking:
			return
		else:
			self.checking = True

		self.tray_icon.set_from_pixbuf(self.busy_icon)
		self.menu.hide_all()
		
		while gtk.events_pending():
			gtk.main_iteration(True)

		newmsgs = self.reddit.get_new_mail()
		if newmsgs:
			# Add newmsgs at the beginning so the latest message is always at index 0
			self.newmsgs = newmsgs + self.newmsgs

			if SHOW_NOTIFICATIONS:
				latestmsg = newmsgs[0]
				title = 'You have a new message on reddit!'
				body  = '<b>%s</b>\n%s' % (latestmsg['subject'], latestmsg['body'])

				balloon = pynotify.Notification(title, body)
				balloon.set_timeout(60*1000)
				balloon.set_icon_from_pixbuf(self.reddit_icon)
				balloon.attach_to_status_icon(self.tray_icon)
				balloon.show()

		if self.newmsgs:
			self.tray_icon.set_from_pixbuf(self.new_mail_icon)
			if len(self.newmsgs) == 1:
				self.tray_icon.set_tooltip('1 new message!')
			else:
				self.tray_icon.set_tooltip('%d new messages!' % len(self.newmsgs))
		else:
			self.tray_icon.set_from_pixbuf(self.reddit_icon)
			self.tray_icon.set_tooltip('No new messages.')

		self.menu.show_all()

		self.checking = False

		# Keep timeout alive
		return True


def open_url(url):
    try:
        subprocess.call(['xdg-open', url])
    except OSError:
        try:
        	import webbrowser
        	webbrowser.open_new_tab(url)
        Except ImportError:
        	# TODO: Throw an error dialog?
        	print "This feature requires the xdg-utils package or Python 2.5 or later."
        

	
if __name__=='__main__':

	cfg_dlg = RedditConfigWindow()

	tray_icon = RedditTrayIcon(
		cfg_dlg.get_username(),
		cfg_dlg.get_password(),
		int(cfg_dlg.get_interval()) * 60000
	)

	tray_icon.on_check_now()
	
	gtk.main()

