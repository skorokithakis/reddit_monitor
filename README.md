What is it?
-----------

Reddit Monitor is a small Python and GTK+ program to notifiy you if you have a
new private message or comment reply on [reddit](http://reddit.com/). It also
comes with a small Python script to allow you to display your reddit karma etc.
in [conky](http://conky.sourceforge.net/) or in a terminal.

Distributed under the terms of the GNU GPL version 3.


Dependencies
------------

    python                          2.x
    python-gtk2                     2.12
    python-notify                   ?  
    python-simplejson               ?
    python-clientcookie (optional)  ?


How to get it?
--------------

The latest stable version of Reddit Monitor can always be found here:
    
[http://davekeogh.github.com/](http://davekeogh.github.com/)

The development version can be checked out with this command:
    
    git clone git://github.com/davekeogh/reddit_monitor.git


Installation
------------

Something similar to the following should install Reddit Monitor for you:

    tar xzf reddit_monitor-0.1.0.tar.gz
    cd reddit_monitor-0.1.0
    [Become root if necessary]
    ./install.py --prefix=/usr


How to report bugs?
-------------------

You can add bug reports, patches, or feature requests to the issue tracker:

[http://github.com/davekeogh/reddit_monitor/issues](http://github.com/davekeogh/reddit_monitor/issues)

