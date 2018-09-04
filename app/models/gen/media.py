'''
Created on 22.7.2017

@author: jorma-h
'''

from sys import stderr
from models.cypher_gramps import Cypher_media_w_handle
import shareds

class Media:
    """ Tallenne
            
        Properties:
                handle          
                change
                id              esim. "O0001"
                uniq_id         int database key
                src             str tallenteen polku
                mime            str tallenteen tyyppi
                description     str tallenteen kuvaus
     """

    def __init__(self):
        """ Luo uuden media-instanssin """
        self.uniq_id = None
        self.handle = ''
        self.change = 0
        self.id = ''
        
        
    @staticmethod
    def get_medias(uniq_id):
        """ Lukee kaikki tallenteet tietokannasta """
                        
        if uniq_id:
            query = "MATCH (o:Media) WHERE ID(o)=$id RETURN ID(o) AS uniq_id, o"
            return  shareds.driver.session().run(query, id=int(uniq_id))
        else:
            query = "MATCH (o:Media) RETURN ID(o) AS uniq_id, o"
            return  shareds.driver.session().run(query)
            


    def get_data(self):
        """ Luetaan tallenteen tiedot """

        query = """
            MATCH (obj:Media)
                WHERE ID(obj)={}
                RETURN obj
            """.format(self.uniq_id)
        obj_result = shareds.driver.session().run(query)

        for obj_record in obj_result:
            self.id = obj_record["obj"]["id"]
            self.change = obj_record["obj"]["change"]
            self.src = obj_record["obj"]["src"]
            self.mime = obj_record["obj"]["mime"]
            self.description = obj_record["obj"]["description"]
                    
        return True
                
        
    @staticmethod
    def get_total():
        """ Tulostaa tallenteiden määrän tietokannassa """
                        
        query = """
            MATCH (o:Media) RETURN COUNT(o)
            """
            
        results =  shareds.driver.session().run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Note*****")
        print ("Handle: " + self.handle)
        print ("Change: {}".format(self.change))
        print ("Id: " + self.id)
        print ("Src: " + self.src)
        print ("Mime: " + self.mime)
        print ("Description: " + self.description)
        return True


    def save(self, tx):
        """ Saves this Media object to db """

        try:
            m_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "src": self.src,
                "mime": self.mime,
                "description": self.description
            }
            return tx.run(Cypher_media_w_handle.create, m_attr=m_attr)

        except Exception as err:
            print("Virhe (Media.save): {0}".format(err), file=stderr)
            raise SystemExit("Stopped due to errors")    # Stop processing
            #TODO raise ConnectionError("Media.save: {0}".format(err))
