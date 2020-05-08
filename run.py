#!/usr/bin/python
# coding=UTF-8

import os

if os.geteuid() < 1000:
    import sys
    sys.path.insert(0, os.path.join(os.getcwd(),"app"))
    from app import app as application
    # application.secret_key = "You don't know OUR secret key"
else:
    if __name__ == '__main__':
        import logging
        neo4j_log = logging.getLogger("neo4j.bolt")
        neo4j_log.setLevel(logging.WARNING)
        from app import app
        app.run()
