'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''
import datetime
from sys import stderr
import logging
from flask import g
import models.dbutil


class Family:
    """ Perhe
            
        Properties:
                handle          
                change
                id              esim. "F0001"
                rel_type        str suhteen tyyppi
                father          str isän osoite
                mother          str äidin osoite
                eventref_hlink  str tapahtuman osoite
                eventref_role   str tapahtuman rooli
                childref_hlink  str lapsen osoite
     """

    def __init__(self):
        """ Luo uuden family-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        self.eventref_hlink = []
        self.eventref_role = []
        self.childref_hlink = []
    
    
    def get_children(self):
        """ Luetaan perheen lasten tiedot """
                        
        query = """
            MATCH (family:Family)-[r:CHILD]->(p:Person)
                WHERE family.gramps_handle='{}'
                RETURN p.gramps_handle AS children
            """.format(self.handle)
        return  g.driver.session().run(query)
    
    
    def get_children_by_id(self):
        """ Luetaan perheen lasten tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)-[r:CHILD]->(person:Person)
  WHERE ID(family)=$pid
RETURN ID(person) AS children"""
        return  g.driver.session().run(query, {"pid": pid})
    
    
    def get_event_data(self):
        """ Luetaan perheen tapahtumien tiedot """
                        
        query = """
            MATCH (family:Family)-[r:EVENT]->(event:Event)
                WHERE family.gramps_handle='{}'
                RETURN r.role AS eventref_role, event.gramps_handle AS eventref_hlink
            """.format(self.handle)
        return  g.driver.session().run(query)
    
    
    def get_event_data_by_id(self):
        """ Luetaan perheen tapahtumien tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)-[r:EVENT]->(event:Event)
  WHERE ID(family)=$pid
RETURN r.role AS eventref_role, event.gramps_handle AS eventref_hlink"""
        return  g.driver.session().run(query, {"pid": pid})
    
    
    def get_family_data(self):
        """ Luetaan perheen tiedot """
        
        global session
                
        query = """
            MATCH (family:Family)
                WHERE family.gramps_handle='{}'
                RETURN family
            """.format(self.handle)
        family_result = g.driver.session().run(query)
        
        for family_record in family_result:
            self.change = family_record["family"]['change']
            self.id = family_record["family"]['id']
            self.rel_type = family_record["family"]['rel_type']
            
        father_result = self.get_father()
        for father_record in father_result:            
            self.father = father_record["father"]

        mother_result = self.get_mother()
        for mother_record in mother_result:            
            self.mother = mother_record["mother"]

        event_result = self.get_event_data()
        for event_record in event_result:            
            self.eventref_hlink.append(event_record["eventref_hlink"])
            self.eventref_role.append(event_record["eventref_role"])

        children_result = self.get_children()
        for children_record in children_result:            
            self.childref_hlink.append(children_record["children"])
            
        return True
    
    
    def get_family_data_by_id(self):
        """ Luetaan perheen tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)
  WHERE ID(family)=$pid
RETURN family"""
        family_result = g.driver.session().run(query, {"pid": pid})
        
        for family_record in family_result:
            self.change = family_record["family"]['change']
            self.id = family_record["family"]['id']
            self.rel_type = family_record["family"]['rel_type']
            
        father_result = self.get_father_by_id()
        for father_record in father_result:            
            self.father = father_record["father"]

        mother_result = self.get_mother_by_id()
        for mother_record in mother_result:            
            self.mother = mother_record["mother"]

        event_result = self.get_event_data_by_id()
        for event_record in event_result:            
            self.eventref_hlink.append(event_record["eventref_hlink"])
            self.eventref_role.append(event_record["eventref_role"])

        children_result = self.get_children_by_id()
        for children_record in children_result:            
            self.childref_hlink.append(children_record["children"])
            
        return True
    
    
    def get_father(self):
        """ Luetaan perheen isän tiedot """
        
        global session
                
        query = """
            MATCH (family:Family)-[r:FATHER]->(p:Person)
                WHERE family.gramps_handle='{}'
                RETURN p.gramps_handle AS father
            """.format(self.handle)
        return  g.driver.session().run(query)
    
    
    def get_father_by_id(self):
        """ Luetaan perheen isän tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)-[r:FATHER]->(person:Person)
  WHERE ID(family)=$pid
RETURN ID(person) AS father"""
        return  g.driver.session().run(query, {"pid": pid})
    
    
    def get_mother(self):
        """ Luetaan perheen äidin tiedot """
        
        global session
                
        query = """
            MATCH (family:Family)-[r:MOTHER]->(p:Person)
                WHERE family.gramps_handle='{}'
                RETURN p.gramps_handle AS mother
            """.format(self.handle)
        return  g.driver.session().run(query)
    
    
    def get_mother_by_id(self):
        """ Luetaan perheen äidin tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)-[r:MOTHER]->(person:Person)
  WHERE ID(family)=$pid
RETURN ID(person) AS mother"""
        return  g.driver.session().run(query, {"pid": pid})
        
    
    @staticmethod       
    def get_total():
        """ Tulostaa perheiden määrän tietokannassa """
        
        global session
                
        query = """
            MATCH (f:Family) RETURN COUNT(f)
            """
        results =  g.driver.session().run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Family*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Rel: " + self.rel_type)
        print ("Father: " + self.father)
        print ("Mother: " + self.mother)
        if len(self.eventref_hlink) > 0:
            for i in range(len(self.eventref_hlink)):
                print ("Eventref_hlink: " + self.eventref_hlink[i])
        if len(self.eventref_role) > 0:
            for i in range(len(self.eventref_role)):
                print ("Role: " + self.eventref_role[i])
        if len(self.childref_hlink) > 0:
            for i in range(len(self.childref_hlink)):
                print ("Childref_hlink: " + self.childref_hlink[i])
        return True


    def save(self):
        """ Tallettaa sen kantaan """

        try:
            query = """
                CREATE (n:Family) 
                SET n.gramps_handle='{}', 
                    n.change='{}', 
                    n.id='{}', 
                    n.rel_type='{}'
                """.format(self.handle, self.change, self.id, self.rel_type)
                
            g.driver.session().run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Person node
            if self.father != '':
                query = """
                    MATCH (n:Family) WHERE n.gramps_handle='{}'
                    MATCH (m:Person) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:FATHER]->(m)
                     """.format(self.handle, self.father)
                                 
                g.driver.session().run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Person node
            if self.mother != '':
                query = """
                    MATCH (n:Family) WHERE n.gramps_handle='{}'
                    MATCH (m:Person) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:MOTHER]->(m)
                     """.format(self.handle, self.mother)
                                 
                g.driver.session().run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        # Make relation(s) to the Event node
        if len(self.eventref_hlink) > 0:
            for i in range(len(self.eventref_hlink)):
                try:
                    query = """
                        MATCH (n:Family) WHERE n.gramps_handle='{}'
                        MATCH (m:Event) WHERE m.gramps_handle='{}'
                        MERGE (n)-[r:EVENT]->(m)
                         """.format(self.handle, self.eventref_hlink[i])
                                 
                    g.driver.session().run(query)
                except Exception as err:
                    print("Virhe: {0}".format(err), file=stderr)
                
                try:
                    query = """
                        MATCH (n:Family)-[r:EVENT]->(m:Event)
                            WHERE n.gramps_handle='{}' AND m.gramps_handle='{}'
                        SET r.role ='{}'
                         """.format(self.handle, self.eventref_hlink[i], self.eventref_role[i])
                                 
                    g.driver.session().run(query)
                except Exception as err:
                    print("Virhe: {0}".format(err), file=stderr)
  
        # Make relation(s) to the Person node
        if len(self.childref_hlink) > 0:
            for i in range(len(self.childref_hlink)):
                try:
                    query = """
                        MATCH (n:Family) WHERE n.gramps_handle='{}'
                        MATCH (m:Person) WHERE m.gramps_handle='{}'
                        MERGE (n)-[r:CHILD]->(m)
                        MERGE (n)<-[s:FAMILY]-(m)
                         """.format(self.handle, self.childref_hlink[i])
                                 
                    g.driver.session().run(query)
                except Exception as err:
                    print("Virhe: {0}".format(err), file=stderr)
            
        return


class Family_for_template(Family):
    """ Templaten perhe perii Perhe luokan
            
        Properties:
                father_data     str isän tiedot
                mother_data     str äidin tiedot
                spouse_data     str puolisoiden tiedot
                children_data   str lasten tiedot
     """

    def __init__(self):
        """ Luo uuden family_for_template-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        self.eventref_hlink = []
        self.eventref_role = []
        self.childref_hlink = []
        self.father_data = ''
        self.mother_data = ''
        self.spouse_data = ''
        self.children_data = []
        

