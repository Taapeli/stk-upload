'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''
from sys import stderr

class Note:
    """ Huomautus
            
        Properties:
                handle          
                change
                id              esim. "N0001"
                type            str huomautuksen tyyppi
                text            str huomautuksen sisältö
     """

    def __init__(self):
        """ Luo uuden note-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        self.type = ''
        
        
    @staticmethod
    def get_total():
        """ Tulostaa huomautusten määrän tietokannassa """
        
        global session
                
        query = """
            MATCH (n:Note) RETURN COUNT(n)
            """
            
        results =  session.run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Note*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Type: " + self.type)
        print ("Text: " + self.text)
        return True


    def save(self):
        """ Tallettaa sen kantaan """

        global session

        try:
            query = """
                CREATE (n:Note) 
                SET n.gramps_handle='{}', 
                    n.change='{}', 
                    n.id='{}', 
                    n.type='{}', 
                    n.text='{}'
                """.format(self.handle, self.change, self.id, self.type, self.text)
                
            return session.run(query)
        except Exception as err:
            print("Virhe {}: {}".format(err.__class__.__name__, str(err), file=stderr))
            raise SystemExit("Stopped due to errors")    # Stop processing
