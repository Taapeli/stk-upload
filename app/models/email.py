import smtplib

import shareds
import logging
import traceback


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

def email_admin(subject,body):
    mail_from = shareds.app.config.get('ADMIN_EMAIL_FROM')
    mail_to = shareds.app.config.get('ADMIN_EMAIL_TO')
    if mail_from and mail_to:
        email(mail_from,mail_to,subject,body)