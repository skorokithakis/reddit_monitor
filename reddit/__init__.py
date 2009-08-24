#Reddit.py, a python lib capable of telling determining if you have a new reddit message.
#Written by Phillip (Philluminati) Taylor. Mail to: Phillip.Taylor@bcs.org.uk
#Licensed under the GNU General Public License version 3. Copies of the license can be found online.

import cookielib, re, urllib, urllib2

# Turns out simplejson is included in Python 2.6 and up as json.
try:
    import json as simplejson
except ImportError:
    try:
        import simplejson
    except ImportError:
        raise ImportError('No module named json or simplejson')

REDDIT_USER_AGENT = { 'User-agent': 'Mozilla/4.0 (compatible; MSIE5.5; Windows NT' }
REDDIT_LOGIN_URL = 'http://www.reddit.com/api/login'
REDDIT_INBOX_PAGE = 'http://www.reddit.com/message/inbox/.json'
REDDIT_PROFILE_PAGE = 'http://www.reddit.com/user/%s/'

#Notes:
#1. Could have better exception handling (i.e. some for 404, wrong password, other basic things)
#2. Could possibly save cookie and reuse it later (no password question on load).
#3. Known bug. If you write a comment on reddit about the regex's this page uses you inadvertantly
#   trick it. (e.g. put /static/mailgrey/png) in a comment and it will wrongly think you have no new
#   mail.

class RedditInvalidUsernamePasswordException(Exception):
    pass

class RedditNotLoggedInException(Exception):
    pass

class RedditBadJSONException(Exception):
    pass

class Reddit(object):
    
    # Unfortunately there's no way to get 
    karma_re = re.compile('<b>(\d+)</b></li><li class="comment-karma">comment karma: &#32;<b>(\d+)</b>')
    
    user = None
    
    def __init__(self):
        #Because the login is an ajax post before we need cookies.
        #That's what made this code annoying to write.
        
        cookie_jar = cookielib.LWPCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
        urllib2.install_opener(opener)
        
    def login(self, user, passwd):
        self.user = user
        
        params = urllib.urlencode({
            'id' : '#login_login-main',
            'op' : 'login-main',
            'passwd' : passwd,
            'user' : user
        })
        
        try:
            req = urllib2.Request(REDDIT_LOGIN_URL, params, REDDIT_USER_AGENT)
            retval = urllib2.urlopen(req).read()
        except Exception, e:
            print "F*CK: %s", e.message
            return False
        
        if retval.find('invalid password') != -1:
            self.logged_in = False
            raise RedditInvalidUsernamePasswordException('Log in failed. Please ensure that your username and password are correct.')
        else:
            self.logged_in = True
        
        return True
        
    #if user == None then it tells you your own karma (provided you called login())
    #Returns a tuple (karma, comment_karma)
    def get_karma(self, user=None):
        if user == None and not self.logged_in:
            raise RedditNotLoggedInException('You must either specify a username or log in to get karma values.')
        
        if user == None:
            user = self.user
        
        try:
            req = urllib2.Request(REDDIT_PROFILE_PAGE % user, None, REDDIT_USER_AGENT)
            page_contents = urllib2.urlopen(req).read()            
        
        except Exception, e:
            print 'Error is related to reading a profile page: %s' % e.message
            raise
        
        results = self.karma_re.search(page_contents)
        karma = int(results.group(1))
        comment_karma = int(results.group(2))

        return (karma, comment_karma)


    def get_new_mail(self):
        if not self.logged_in:
            raise RedditNotLoggedInException('You must be logged in to check for new messages.')
        
        try:
            req = urllib2.Request(REDDIT_INBOX_PAGE, None, REDDIT_USER_AGENT)
            json_data = urllib2.urlopen(req).read()
        
        except Exception, e:
            print 'Error is related to reading inbox page: %s' % e.message
            raise
        
        try:
            inbox = simplejson.loads(json_data)
            msgs = inbox['data']['children']
            return [msg['data'] for msg in msgs if msg['data']['new'] == True]
        
        except (KeyError, ValueError):
            raise RedditBadJSONException('The JSON returned from reddit is incomplete. Perhpas the connection was interupted or reddit is down.')
