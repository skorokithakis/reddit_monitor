#!/usr/bin/env python

import sys, re
import reddit

USAGE = '''Usage: reddit_status username password [format string]

The format string needs to contain at least one of the following tokens:
    
    %k    karma score
    %c    comment karma
    %m    new messages
    %u    user name (optional)'''

FORMAT = 'You have %m new messages on reddit.'

class InvalidFormatStringException(Exception):
    pass


def parse_format_string(format_string):
    tokens = re.search('(%[kcm])', format_string)
    
    if tokens:
        return format_string
    else:
        raise InvalidFormatStringException


if __name__ == '__main__':
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print USAGE
        sys.exit(2)
    
    elif len(sys.argv) == 4:
        try:
            format = parse_format_string(sys.argv[3])
        except InvalidFormatStringException:
            print USAGE
            sys.exit(2)
    
    else:
        format = FORMAT
    
    session = reddit.Reddit()
    
    try:
        session.login(sys.argv[1], sys.argv[2])
    except reddit.RedditInvalidUsernamePasswordException:
        print 'Log in failed. Please ensure that your username and password are correct.'
        sys.exit(1)
    
    karma, comment_karma = session.get_karma()
    messages = len(session.get_new_mail())
    
    format = format.replace('\\n', '\n')
    format = format.replace('%k', str(karma))
    format = format.replace('%c', str(comment_karma))
    format = format.replace('%m', str(messages))
    format = format.replace('%u', sys.argv[1])
    
    print format
    sys.exit(0)
