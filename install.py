#!/usr/bin/env python

import sys, os, subprocess, optparse, distutils


APPLICATION = 'Reddit Monitor'
VERSION = '0.1.0'
PREFIX = '/usr'
REMOVE = False

DIRECTORIES = ('share/reddit_monitor', 'share/reddit_monitor/icons')

FILES = {
    'reddit_tray_icon.ui'           : DIRECTORIES[0],
    'reddit_monitor.desktop'        : 'share/applications',
    'reddit_monitor'                : 'bin',
    'reddit_status'                 : 'bin',
    'icons/busy.gif'                : DIRECTORIES[1],
    'icons/new_mail.png'            : DIRECTORIES[1],
    'icons/new_mail_trans.png'      : DIRECTORIES[1],
    'icons/reddit.png'              : DIRECTORIES[1],
    'icons/reddit_border_trans.png' : DIRECTORIES[1],
    'icons/reddit_trans.png'        : DIRECTORIES[1],
    'reddit.py'                     : 'lib/python%s.%s/dist-packages/' % (sys.version_info[0], sys.version_info[1]),
    'egg_tray_icon.py'              : 'lib/python%s.%s/dist-packages/' % (sys.version_info[0], sys.version_info[1]),
}


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--prefix', dest='prefix', help='define an alternate location to install to')
    parser.add_option('--remove', '-r', action='store_true', dest='remove', help='remove any installed files')
    
    options = parser.parse_args()[0]
    
    if options.remove:
        REMOVE = options.remove
    
    if options.prefix:
        PREFIX = options.prefix

    if not REMOVE:
        print 'Installing %s %s :\n' % (APPLICATION, VERSION)

        for dir in DIRECTORIES:
            print 'Creating directory %s ...' % os.path.join(PREFIX, dir) ,
            if subprocess.call(['mkdir', '-p', os.path.join(PREFIX, dir)]):
                print 'Failed'
                print '\n%s failed to install.' % APPLICATION
                sys.exit(1)
            else:
                print 'Done'
        
        for file in FILES:
            print 'Copying %s to %s ...' % (file, os.path.join(PREFIX, FILES[file])) ,
            if subprocess.call(['install', file, os.path.join(PREFIX, os.path.join(FILES[file], file))]):
                print 'Failed'
                print '\n%s failed to install.' % APPLICATION
                sys.exit(1)
            else:
                print 'Done'

        print '\n%s %s is now installed.' % (APPLICATION, VERSION)
    
    else:
        print 'Uninstalling %s %s :\n' % (APPLICATION, VERSION)
        
        for file in FILES:
            print 'Removing %s ...' % os.path.join(PREFIX, os.path.join(FILES[file], file)) ,
            if subprocess.call(['rm', os.path.join(PREFIX, os.path.join(FILES[file], file))]):
                print 'Failed'
                print '\nFailed to uninstall %s.' % APPLICATION
                sys.exit(1)
            else:
                print 'Done'
        
        for dir in DIRECTORIES:
            print 'Removing directory %s ...' % os.path.join(PREFIX, dir) ,
            if subprocess.call(['rm', '-rf', os.path.join(PREFIX, dir)]):
                print 'Failed'
                print '\n%s failed to install.' % APPLICATION
                sys.exit(1)
            else:
                print 'Done'
        
        print '\n%s %s has been uninstalled.' % (APPLICATION, VERSION)
