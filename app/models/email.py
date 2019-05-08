import smtplib

import shareds
import logging
import traceback

from flask_mail import Mail, Message
from models import syslog

def email(mail_from,mail_to,subject,body):
    try:
        mail = Mail()
        msg = Message(subject,
                      body=body,
                      sender=mail_from,
                      reply_to=mail_from,
                      recipients=[mail_to])
        mail.send(msg)
    except Exception as e:
        logging.error("iError in sending email")
        logging.error(str(e))
        traceback.print_exc()

def email_admin(subject,body,sender=None):
    if sender is None:
        sender = shareds.app.config.get('ADMIN_EMAIL_FROM')
    mail_to = shareds.app.config.get('ADMIN_EMAIL_TO')
    if sender and mail_to:
        email(sender,mail_to,subject,body)
        syslog.log(type="sent email to admin",sender=sender,receiver=mail_to,subject=subject)    
        
def email_from_admin(subject,body,receiver):
    sender = shareds.app.config.get('ADMIN_EMAIL_FROM')
    if sender:
        email(sender,receiver,subject,body)    
        syslog.log(type="sent email from admin",sender=sender,receiver=receiver,subject=subject)    