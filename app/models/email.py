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

import smtplib

import shareds
import logging
import traceback

from flask_mail import Mail, Message
from models import syslog
#from builtins import False

def get_sysname():
    sysname = shareds.app.config.get("STK_SYSNAME")
    return sysname

def email(mail_from,mail_to,subject,body):
    try:
        mail = Mail()
        sysname = get_sysname()
        msg = Message(f"{subject} ({sysname})",
                      body=body,
                      sender=mail_from,
                      reply_to=mail_from,
                      recipients=[mail_to])
        mail.send(msg)
        return True
    except Exception as e:
        logging.error("iError in sending email")
        logging.error(str(e))
        traceback.print_exc()
    return False

def email_admin(subject,body,sender=None):
    if sender is None:
        sender = shareds.app.config.get('ADMIN_EMAIL_FROM')
    mail_to = shareds.app.config.get('ADMIN_EMAIL_TO')
    if sender and mail_to:
        if email(sender,mail_to,subject,body):
            syslog.log(type="sent email to admin", sender=sender,receiver=mail_to,subject=subject)
            return True
        else:    
            syslog.log(type="FAILED: email to admin", sender=sender,receiver=mail_to,subject=subject)
            return False
    return False
        
def email_from_admin(subject,body,receiver):
    sender = shareds.app.config.get('ADMIN_EMAIL_FROM')
    if sender:
        syslog.log(type="sent email from admin",sender=sender,receiver=receiver,subject=subject)    
        return email(sender,receiver,subject,body)    
