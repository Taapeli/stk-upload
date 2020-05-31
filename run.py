#!/usr/bin/python
# coding=UTF-8

import os
import platform

# On linux system uids are < 1000.  I know nothin about windows uids.
# This should tell if we are on server or developer enviroment:
running_on_server = ((platform.system() == "Linux") and (os.getuid() < 1000))
#running_on_server = os.path.isdir('/var/log/httpd/stkserver')

if running_on_server:
    import sys
    sys.path.insert(0, os.path.join(os.getcwd(),"app"))
    from app import app as application
    application.secret_key = "You don'n know OUR secret key"
else:
    if __name__ == '__main__':
        import logging
        neo4j_log = logging.getLogger("neo4j.bolt")
        neo4j_log.setLevel(logging.WARNING)
        from app import app
        app.run()
