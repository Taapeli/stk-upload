'''
Created on 22.7.2017

@author: jorma-h
'''

from sys import stderr
from flask import g
import models.dbutil


class Object:
    """ Tallenne
            
        Properties:
                handle          
                change
                id              esim. "O0001"
                src             str tallenteen polku
                mime            str tallenteen tyyppi
                description     str tallenteen kuvaus
     """

    def __init__(self):
        """ Luo uuden object-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        
        
    @staticmethod
    def get_objects(uniq_id):
        """ Lukee kaikki tallenteet tietokannasta """
                        
        if uniq_id:
            where = "WHERE ID(object)={} ".format(uniq_id)
        else:
            where = ''

        query = """
            MATCH (o:Object) {0} RETURN ID(o) AS uniq_id, o
            """.format(where)
            
        return  g.driver.session().run(query)


    def get_object_data_by_id(self):
        """ Luetaan tallenteen tiedot """

        query = """
            MATCH (obj:Object)
                WHERE ID(obj)={}
                RETURN obj
            """.format(self.uniq_id)
        obj_result = g.driver.session().run(query)

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
            MATCH (o:Object) RETURN COUNT(o)
            """
            
        results =  g.driver.session().run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Note*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Src: " + self.src)
        print ("Mime: " + self.mime)
        print ("Description: " + self.description)
        return True


    def save(self, tx):
        """ Tallettaa sen kantaan """

        try:
            query = """
                CREATE (o:Object) 
                SET o.gramps_handle='{}', 
                    o.change='{}', 
                    o.id='{}', 
                    o.src='{}', 
                    o.mime='{}', 
                    o.description='{}'
                """.format(self.handle, self.change, self.id, 
                           self.src, self.mime, self.description)
                
            return tx.run(query)
        except Exception as err:
            print("Virhe {}: {}".format(err.__class__.__name__, str(err), file=stderr))
            raise SystemExit("Stopped due to errors")    # Stop processing
