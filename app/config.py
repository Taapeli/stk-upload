'''
Created on 17.11.2017

@author: TimNal

Sovelluksen toiminnallisuutta ohjaavat tiedot  
'''
  
print('Luetaan sovelluksen config.py')
DEBUG = False
SECURITY_REGISTERABLE = True
SECURITY_CONFIRMABLE = True
SECURITY_RECOVERABLE = True
SECURITY_TRACKABLE = True
#SECURITY_REGISTER_URL = '/register'
#SECURITY_SEND_CONFIRMATION_TEMPLATE = 'stk_security/send_confirmation.html' 
#SECURITY_LOGIN_USER_TEMPLATE = 'login/logged.html'
SECURITY_POST_LOGIN_VIEW = '/'
SECURITY_POST_LOGOUT_VIEW = 'login'
#SECURITY_REGISTER_USER_TEMPLATE = 'stk_security/register_user.html'
#SECURITY_RESET_PASSWORD_TEMPLATE = 'stk_security/reset_password.html'
#SECURITY_CHANGE_PASSWORD_TEMPLATE = 'stk_security/change_password.html'
SECURITY_SEND_REGISTER_EMAIL = True

DEFAULT_ROLE='admin'
EXPLAIN_TEMPLATE_LOADING=False   # Explain Flask, if you like
