'''
Created on 22.12.2019

@author: nalli
'''
from flask_security import utils as sec_utils
inp="taapeli"
ot=b"dGFhcGVsaQ=="
decoded = sec_utils.hash_password(inp)
print(decoded)
