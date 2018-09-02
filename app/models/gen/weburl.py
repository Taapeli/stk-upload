'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''


class Weburl():
    """ A web reference 

        Properties:
                priv           str url salattu tieto
                href           str url osoite
                type           str url tyyppi
                description    str url kuvaus
    """

    def __init__(self, href=None, rtype=None, description=""):
        """ Luo uuden weburl-instanssin """
        self.href = href
        self.type = rtype
        self.description = description
        self.priv = ""
# Previous:
#         self.url_href = href
#         self.url_type = rtype
#         self.url_description = description

    def __str__(self):
        desc = "Weburl ({}) '{}' > '{}'".format(self.type, self.description, self.href)
        return desc

