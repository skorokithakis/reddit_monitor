#!/usr/bin/python

from distutils.core import setup

setup(
    version = '0.1.0',
    name = 'reddit_monitor',
    
    packages = [
        'reddit',
    ],
    
    scripts = [
        'reddit_monitor',
        'reddit_status'
    ],
    
    data_files = [
        ('share/applications', 'reddit_monitor.desktop'),
        ('share/reddit_monitor', 'reddit_tray_icon.ui'),
        ('share/reddit_monitor/icons', 'icons/busy.gif'),
        ('share/reddit_monitor/icons', 'icons/new_mail.png')
        ('share/reddit_monitor/icons', 'icons/new_mail_trans.png')
        ('share/reddit_monitor/icons', 'icons/reddit.png')
        ('share/reddit_monitor/icons', 'icons/reddit_border_trans.gif')
        ('share/reddit_monitor/icons', 'icons/reddit_trans.gif')
    ],
    
    description='Notifies you when you have new messages on reddit.',
    license='GNU GPL version 3',
    url='http://github.com/davekeogh/reddit_monitor/tree/master',
    author='David Keogh',
    author_email='davekeogh@shaw.ca',
    long_description='Reddit Monitor is a small Python and GTK+ program to notifiy you if you have a new private message or comment reply on reddit. It also comes with a small Python script to allow you to display your reddit karma and number of new messages in conky or in a terminal.',
)
