'''
    Weburl class represents Web url reference 
    
    () -[r:WEBREF]-> (w:Weburl)
    () -[:WEBREF{type: "Web Search", priv: "", desc: "Haminan kaupunki"}]-> 
       (:Weburl {href: "https://www.hamina.fi/"})

Created on 3.8.2018

@author: Juha Mäkeläinen <jpek@iki.fi>
'''

from sys import stderr

from .cypher import Cypher_weburl

class Weburl():
    """ A web reference 

        Properties:
                priv           str url salattu tieto
                href           str url osoite
                type           str url tyyppi
                description    str url kuvaus
    """

    def __init__(self):
        """ Creates a new weburl instance
        """
        self.href = None
        self.type = None
        self.description = ""
        self.priv = ""

    @staticmethod
    def from_record(record):
        ''' Create Weburl from a collection in Neo4j result
        # collect([w.href, wr.type, wr.description, wr.priv]) as webref
        '''
        if record[0] != None:   # Must have href
            return None
        url = Weburl()
        url.href = record[0]
        url.type = record[1]
        url.description = record[2]
        url.priv = record[3]
        return url

    def __str__(self):
        return "{} '{}' <{}>".format(self.type, self.description, self.href)


    def save(self, tx, parent_id=None):
        """ Saves a Weburl and creates a link from patent id
        """
        if parent_id == None:
            msg = "Error Repository.save weburl: no parent_id"
            print(msg, file=stderr)
            raise SystemExit(msg)    # Stop processing
        try:
            result = tx.run(Cypher_weburl.link_to_weburl, parent_id=parent_id,
                            href=self.href, type=self.type, 
                            desc=self.description, priv=self.priv)
            res = result.single()
            print("Luotiin ({})-[{}]->(:Weburl {})".\
                  format(parent_id, res['weburl_id'], res['ref_id']))
        except Exception as err:
            print("Error Repository.save weburl: {0}".format(err), file=stderr)
            raise SystemExit("Stopped due to errors")    # Stop processing
            #TODO raise ConnectionError("Repository.save: {0}".format(err))
