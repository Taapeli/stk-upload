import smtplib

import shareds
import logging
import traceback

from models import syslog

def email(mail_from,mail_to,subject,body):
    msg = """\
From: %s
Subject: %s
To: %s

%s
""" % (mail_from,subject,mail_to,body)
    #print msg
    try:
        mail_server = shareds.app.config['MAIL_SERVER']
        conn = smtplib.SMTP(mail_server)
        conn.set_debuglevel(True)
        msg = msg.encode("utf-8",errors='ignore')
        conn.sendmail(mail_from, [mail_to], msg)
        conn.quit()
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