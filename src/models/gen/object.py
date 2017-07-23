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
            
        result =  g.driver.session().run(query)
        
        titles = ['uniq_id', 'gramps_handle', 'change', 'id', 
                  'src', 'mime', 'description']
        objects = []
        
        for record in result:
            note_line = []
            if record['uniq_id']:
                note_line.append(record['uniq_id'])
            else:
                note_line.append('-')
            if record["o"]['gramps_handle']:
                note_line.append(record["n"]['gramps_handle'])
            else:
                note_line.append('-')
            if record["o"]['change']:
                note_line.append(record["n"]['change'])
            else:
                note_line.append('-')
            if record["o"]['id']:
                note_line.append(record["n"]['id'])
            else:
                note_line.append('-')
            if record["o"]['src']:
                note_line.append(record["n"]['src'])
            else:
                note_line.append('-')
            if record["o"]['mime']:
                note_line.append(record["n"]['mime'])
            else:
                note_line.append('-')
            if record["o"]['description']:
                note_line.append(record["n"]['description'])
            else:
                note_line.append('-')
                                
            objects.append(note_line)
                
        return (titles, objects)
        
        
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
