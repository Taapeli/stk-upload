#!/usr/bin/python
# coding=UTF-8


import sys
import os
import logging

class ContextFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.
    """

    def __init__(self):
        self.user = "<Nobody>" # choice(ContextFilter.USERS)

    def filter(self, record):
        if hasattr(self,'user'):
            record.user = self.user
        else:
            record.user = '-'
            print("# setups.ContextFilter.filter: 'user' not defined")
        return True

formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(user)s %(message)s')

# Are we running on production/test server or developer enviroment?
serverlog_dir = '/var/log/httpd/stkserver'
running_on_server = os.path.isdir(serverlog_dir)
if running_on_server:
    fh = logging.FileHandler(serverlog_dir + '/stkserver.log')
else:
    fh = logging.FileHandler('/tmp/stkserver.log')
    # fh = logging.FileHandler(os.getcwd() + "/../stk-serverlogs/stkserver.log")
    neo4j_log = logging.getLogger("neo4j.bolt")
    neo4j_log.setLevel(logging.WARNING)

fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger = logging.getLogger('stkserver')
logger.setLevel(logging.DEBUG)
logger.addFilter(ContextFilter())
logger.addHandler(fh)

if running_on_server:
    sys.path.insert(0, os.path.join(os.getcwd(),"app"))
    from app import app as application
    application.secret_key = "You don't know OUR secret key"
else:
    if __name__ == '__main__':
        from app import app
        print('Käynnistys: {} logging {} file {}'.format(app, logger, fh.stream.name))
        app.run()
