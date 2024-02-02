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

def xxxemail(mail_from,mail_to,reply_to,subject,body):
    try:
        mail = Mail()
        sysname = get_sysname()
        msg = Message(f"{sysname.title()}: {subject}",
                      body=body,
                      sender=mail_from,
                      reply_to=reply_to,
                      recipients=[mail_to])
        mail.send(msg)
        return True
    except Exception as e:
        logging.error("iError in sending email")
        logging.error(str(e))
        traceback.print_exc()
    return False

def email(mail_from, mail_to, reply_to, subject, body):
    msg = f"""\
From: {mail_from}
Subject: {subject}
To: {mail_to}
Reply-to: {reply_to}

{body}
""" 
    mail_server = shareds.app.config.get('MAIL_SERVER')
    mail_user = shareds.app.config.get('MAIL_USERNAME')
    mail_password = shareds.app.config.get('MAIL_PASSWORD')
    conn = smtplib.SMTP_SSL(mail_server)
    conn.set_debuglevel(True)
    if mail_user:
        conn.login(mail_user, mail_password)
    msg = msg.replace("\n", "\r\n")
    msg = msg.encode("utf-8",errors='ignore')
    conn.sendmail(mail_user, [mail_to], msg)
    conn.quit()
    return True



def email_admin(subject,body,sender=None): # send email to admin
    # must use isotammi.net domain for the sender (Sender Policy Framework)
    admin = shareds.app.config.get('ADMIN_EMAIL_FROM')
    
    mail_to = shareds.app.config.get('ADMIN_EMAIL_TO')
    
    # put the original sender in the 'reply to' address
    if sender is None:
        reply_to = mail_to
    else:
        reply_to = sender
    if admin and mail_to and reply_to:
        if email(admin,mail_to,reply_to,subject,body):
            syslog.log(type="sent email to admin", sender=sender,receiver=mail_to,reply_to=reply_to,subject=subject)
            return True
        else:    
            syslog.log(type="FAILED: email to admin", sender=sender,receiver=mail_to,reply_to=reply_to,subject=subject)
            return False
    return False
        
def email_from_admin(subject,body,receiver):
    sender = shareds.app.config.get('ADMIN_EMAIL_FROM')
    reply_to = shareds.app.config.get('ADMIN_EMAIL_TO')
    if sender and reply_to:
        syslog.log(type="sent email from admin",sender=sender,receiver=receiver,reply_to=reply_to,subject=subject)    
        return email(sender,receiver,reply_to,subject,body)    
