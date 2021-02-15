#!/usr/bin/python
# coding=UTF-8

#   Isotammi Geneological Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
