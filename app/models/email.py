import smtplib

import shareds


def email(mail_from,mail_to,subject,body):
    msg = """\
From: %s
Subject: %s
To: %s

%s
""" % (mail_from,subject,mail_to,body)
    #print msg
    mail_server = shareds.app.config['MAIL_SERVER']
    conn = smtplib.SMTP(mail_server)
    conn.set_debuglevel(True)
    msg = msg.encode("utf-8",errors='ignore')
    conn.sendmail(mail_from, [mail_to], msg)
    conn.quit()
