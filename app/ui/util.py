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


def error_print(module_name:str, e:Exception):
    """ Print error messages to flask.flash, console and logs. 
    """
    traceback.print_exc()  

    msg = f"bp.audit.routes.{module_name}: {e.__class__.__name__} {e}"
    print(msg)
    logger.error(msg)
    flash(f'{_("The operation failed due to error")}: {e}')
