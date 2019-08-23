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
