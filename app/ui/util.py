#   Isotammi Genealogical Service for combining multiple researchers' results.
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
'''
Created on 15.9.2021

@author: jm
'''
import logging
logger = logging.getLogger("stkserver")

import traceback
from flask import flash
from flask_babelex import _

from ui.user_context import UserContext


def stk_logger(context: UserContext, msg: str):
    """Emit logger info message with Use Case mark uc=<code> .
    """
    if not context:
        logger.info(msg)
        return
    uc = context.use_case()
    if (msg[:2] != "->") or (uc == ""):
        logger.info(msg)
        return
    logger.info(f"-> {msg[2:]} uc={uc}")
    return


def error_print(module_name:str, e:Exception, do_flash:bool = True):
    """ Print error messages to flask.flash, console and logs. 
    """
    traceback.print_exc()  

    msg = f"bp.audit.routes.{module_name}: {e.__class__.__name__} {e}"
    print(msg)
    logger.error(msg)
    if do_flash:
        flash(f'{_("The operation failed due to error")}: {e}')
