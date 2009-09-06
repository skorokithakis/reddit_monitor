#!/usr/bin/python

from distutils.core import setup

def make_readme():
    '''Makes a plaintext README file from the markdown version.'''
    pass

def remove_reddit_module():
    '''0.1.0 and 0.2.0 installed a module named reddit which has been replaced
    by redditmonitor. If it's still installed this function will delete it.'''
    pass


setup(
    version = '0.3.0',
    name = 'reddit_monitor',
    
    description = 'Notifies you when you have new messages on reddit.',
    license = 'GNU GPL version 3',
    url = 'http://github.com/davekeogh/reddit_monitor/tree/master',
    author = 'David Keogh',
    author_email = 'davekeogh@shaw.ca',
    long_description = 'Reddit Monitor is a small Python and GTK+ program to notifiy you if you have a new private message or comment reply on reddit. It also comes with a small Python script to allow you to display your reddit karma and number of new messages in conky or in a terminal.',
    
    classifiers = [
        'Intended Audience :: End Users/Desktop',
    ],
    
    packages = [
        'redditmonitor',
    ],
    
    scripts = [
        'reddit_monitor',
        'reddit_status',
    ],
    
    data_files = [
        ('share/applications', ['reddit_monitor.desktop']),
        ('share/reddit_monitor', ['reddit_tray_icon.ui']),
        ('share/pixmaps', ['reddit.png']),
        
        ('share/reddit_monitor/icons', ['icons/busy.gif', 'icons/new_mail.png',
                                        'icons/new_mail_trans.png',
                                        'icons/reddit.png',
                                        'icons/reddit_border_trans.png',
                                        'icons/reddit_trans.png']),
        
        ('share/reddit_monitor/sounds', ['sounds/bell.wav', 
                                         'sounds/message-new-email.wav',
                                         'sounds/message-new-instant.wav',
                                         'sounds/phone-incoming-call.wav',
                                         'sounds/README']),
    ],
)
