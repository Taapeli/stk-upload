#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta, Juha Takala
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

# Flask routes program for Stk application stat blueprint
#
# Juha Takala 08.05.2020 19:11:31

import logging
logger = logging.getLogger('stkserver')
import time

from flask import render_template
from flask_security import roles_accepted, login_required
# from flask_babelex import _

import shareds

from . import bp
from .models import logreader, utils


################################################################
#### @route funtions below

################################################################
#
@bp.route('/stat')
@login_required
@roles_accepted('admin')
def stat_home():
    """Statistics from stk server.
    """
    t0 = time.time()
    res = utils.build_general_stats()
    elapsed = time.time() - t0
    logger.info(f"-> bp.stat e={elapsed:.4f}")
    return render_template("/stat/stat.html",
                           res=res,
                           elapsed=elapsed,
    )

################################################################
#
@bp.route('/stat/appstat', methods = ['GET', 'POST'])
@login_required
@roles_accepted('admin')
def stat_app():
    """Statistics about stk application usage.
    """

    t0 = time.time()

    (pkey, parser, logfiles, opts) = utils.build_options(
        shareds.app.config['STK_LOGFILE'], {
            "msg" : logreader.StkServerlog.save_bymsg,
            "date": logreader.StkServerlog.save_bydate,
            "user": logreader.StkServerlog.save_byuser,
        })

    # res [] could collect results from many logreader invocations, one set
    # from each call (inside loop, as we once did)
    res = []
    # We now have one logreader to read all log files (outside the loop):
    logrdr = logreader.StkServerlog(
        "Top_level", by_what=[(pkey, parser)], opts=opts,
    )
    for f in logfiles:
        logrdr.work_with(f)
    res.append(logrdr.get_report()) # that will be one filesection

    elapsed = time.time() - t0
    logger.info(f"-> bp.stat.app e={elapsed:.4f}")
    return render_template("/stat/appstat.html",
                           h2      = "Application usage statistics",
                           caller  = "/stat/appstat",
                           title   = "App stats",
                           res     = res,
                           opts    = opts,
                           elapsed = elapsed,
    )


################################################################
#
@bp.route('/stat/uploadstat', methods = ['GET', 'POST'])
@login_required
@roles_accepted('admin')
def stat_upload():
    """Statistics about stk uploads.
    """

    t0 = time.time()

    (pkey, parser, logfiles, opts) = utils.build_options(
        "*.log", {
            "msg"   :  logreader.StkUploadlog.save_bymsg,
            "date"  :  logreader.StkUploadlog.save_bydate,
            "user"  :  logreader.StkUploadlog.save_byuser,
        })

    # Create one logreader to read all logfiles
    logrdr = logreader.StkUploadlog(
        "Top_level", by_what=[(pkey, parser)], opts=opts,
    )
    for f in logfiles:
        logrdr.work_with(f)
    res = [logrdr.get_report()] # that will be one filesection for all
                                    # files in the loop

    elapsed = time.time() - t0
    logger.info(f"-> bp.stat.uploadstat e={elapsed:.4f}")
    return render_template("/stat/appstat.html",
                           h2      = "Data upload statistics",
                           caller  = "/stat/uploadstat",
                           title   = "Upload stats",
                           res     = res,
                           opts    = opts,
                           elapsed = elapsed,
    )

