'''
    Person and Name classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

import datetime
from sys import stderr
import logging
from flask import g
import models.dbutil

class Person:
    """ Henkilö
            
        Properties:
                handle          
                change
                uniq_id            int noden id
                id                 esim. "I0001"
                gender             str sukupuoli
                name:
                   alt             str muun nimen nro
                   type            str nimen tyyppi
                   firstname       str etunimi
                   refname         str referenssinimi
                   surname         str sukunimi
                   suffix          str patronyymi
                eventref_hlink     str tapahtuman osoite
                eventref_role      str tapahtuman rooli
                objref_hlink       str tallenteen osoite
                url_href           str url osoite
                url_type           str url tyyppi
                url_description    str url kuvaus
                parentin_hlink     str vanhempien osoite
                citationref_hlink  str viittauksen osoite
     """

    def __init__(self, pid=''):
        """ Luo uuden person-instanssin """
        self.handle = ''
        self.change = ''
        self.uniq_id = 0
        self.id = pid
        self.name = []
        self.gender = ''
        self.events = []                # For creating display sets
        self.eventref_hlink = []        # Gramps event handles
        self.eventref_role = []
        self.objref_hlink = []
        self.url_href = []
        self.url_type = []
        self.url_description = []
        self.parentin_hlink = []
        self.citationref_hlink = []
    
    
    def get_citation_handle(self):
        """ Luetaan henkilön viittauksen handle """
        
        query = """
            MATCH (person:Person)-[r:CITATION]->(c:Citation) 
                WHERE person.gramps_handle='{}'
                RETURN c.gramps_handle AS citationref_hlink
            """.format(self.handle)
        return  g.driver.session().run(query)
    
    
    def get_event_data(self):
        """ Luetaan henkilön tapahtumien handlet """
        
        query = """
            MATCH (person:Person)-[r:EVENT]->(event:Event) 
                WHERE person.gramps_handle='{}'
                RETURN r.role AS eventref_role, event.gramps_handle AS eventref_hlink
            """.format(self.handle)
        return  g.driver.session().run(query)
    
    
    def get_event_data_by_id(self):
        """ Luetaan henkilön tapahtumien id:t """
        
        pid = int(self.uniq_id)
        query = """
MATCH (person:Person)-[r:EVENT]->(event:Event) 
  WHERE ID(person)=$pid
RETURN r.role AS eventref_role, ID(event) AS eventref_hlink"""
        return  g.driver.session().run(query, {"pid": pid})
    
    
    def get_her_families(self):
        """ Luetaan naisen perheiden handlet """
        
        query = """
            MATCH (person:Person)<-[r:MOTHER]-(family:Family) 
                WHERE person.gramps_handle='{}'
                RETURN family.gramps_handle AS handle
            """.format(self.handle)
        return  g.driver.session().run(query)
    
    
    def get_her_families_by_id(self):
        """ Luetaan naisen perheiden id:t """
        
        pid = int(self.uniq_id)
        query = """
MATCH (person:Person)<-[r:MOTHER]-(family:Family) 
  WHERE ID(person)=$pid
RETURN ID(family) AS uniq_id"""
        return  g.driver.session().run(query, {"pid": pid})
    
    
    def get_his_families(self):
        """ Luetaan miehen perheiden handlet """
        
        query = """
            MATCH (person:Person)<-[r:FATHER]-(family:Family) 
                WHERE person.gramps_handle='{}'
                RETURN family.gramps_handle AS handle
            """.format(self.handle)
        return  g.driver.session().run(query)
    
    
    def get_his_families_by_id(self):
        """ Luetaan miehen perheiden id:t """
        
        pid = int(self.uniq_id)
        query = """
MATCH (person:Person)<-[r:FATHER]-(family:Family) 
  WHERE ID(person)=$pid
RETURN ID(family) AS uniq_id"""
        return  g.driver.session().run(query, {"pid": pid})

    
    def get_hlinks(self):
        """ Luetaan henkilön linkit """
            
        event_result = self.get_event_data()
        for event_record in event_result:            
            self.eventref_hlink.append(event_record["eventref_hlink"])
            self.eventref_role.append(event_record["eventref_role"])

        family_result = self.get_parentin_handle()
        for family_record in family_result:            
            self.parentin_hlink.append(family_record["parentin_hlink"])
            
        citation_result = self.get_citation_handle()
        for citation_record in citation_result:            
            self.citationref_hlink.append(citation_record["citationref_hlink"])
            
        return True

    
    def get_hlinks_by_id(self):
        """ Luetaan henkilön linkit """
            
        event_result = self.get_event_data_by_id()
        for event_record in event_result:            
            self.eventref_hlink.append(event_record["eventref_hlink"])
            self.eventref_role.append(event_record["eventref_role"])

        object_result = self.get_object_id()
        for object_record in object_result:            
            self.objref_hlink.append(object_record["objref_hlink"])

        family_result = self.get_parentin_handle()
        for family_record in family_result:            
            self.parentin_hlink.append(family_record["parentin_hlink"])
            
        citation_result = self.get_citation_handle()
        for citation_record in citation_result:            
            self.citationref_hlink.append(citation_record["citationref_hlink"])
            
        return True
    
    
    def get_object_id(self):
        """ Luetaan henkilön tallenteen id """
        
        query = """
            MATCH (person:Person)-[r:OBJECT]->(obj:Object) 
                WHERE ID(person)={}
                RETURN ID(obj) AS objref_hlink
            """.format(self.uniq_id)
        return  g.driver.session().run(query)
    
    
    def get_parentin_handle(self):
        """ Luetaan henkilön perheen handle """
        
        query = """
            MATCH (person:Person)-[r:FAMILY]->(family:Family) 
                WHERE person.gramps_handle='{}'
                RETURN family.gramps_handle AS parentin_hlink
            """.format(self.handle)
        return  g.driver.session().run(query)
    
    
    def get_parentin_id(self):
        """ Luetaan henkilön perheen id """
        
        query = """
            MATCH (person:Person)-[r:FAMILY]->(family:Family) 
                WHERE ID(person)={}
                RETURN ID(family) AS parentin_hlink
            """.format(self.uniq_id)
        return  g.driver.session().run(query)
    
    
    def get_person_and_name_data(self):
        """ Luetaan kaikki henkilön tiedot """
        
        query = """
            MATCH (person:Person)-[r:NAME]-(name:Name) 
                WHERE person.gramps_handle='{}'
                RETURN ID(person) AS id, person, name
                ORDER BY name.alt
            """.format(self.handle)
        person_result = g.driver.session().run(query)
        
        for person_record in person_result:
            self.uniq_id = person_record['id']
            self.change = person_record["person"]['change']
            self.id = person_record["person"]['id']
            self.gender = person_record["person"]['gender']
            
            if len(person_record["name"]) > 0:
                pname = Name()
                pname.alt = person_record["name"]['alt']
                pname.type = person_record["name"]['type']
                pname.firstname = person_record["name"]['firstname']
                pname.refname = person_record["name"]['refname']
                pname.surname = person_record["name"]['surname']
                pname.suffix = person_record["name"]['suffix']
                self.name.append(pname)
    
    
    def get_person_and_name_data_by_id(self):
        """ Luetaan kaikki henkilön tiedot """
        
        pid = int(self.uniq_id)
        query = """
MATCH (person:Person)-[r:NAME]-(name:Name) 
  WHERE ID(person)=$pid
RETURN person, name
  ORDER BY name.alt"""
        person_result = g.driver.session().run(query, {"pid": pid})
        
        for person_record in person_result:
            self.handle = person_record["person"]['handle']
            self.change = person_record["person"]['change']
            self.id = person_record["person"]['id']
            self.gender = person_record["person"]['gender']
            self.url_href = person_record["person"]['url_href']
            self.url_type = person_record["person"]['url_type']
            self.url_description = person_record["person"]['url_description']
            
            if len(person_record["name"]) > 0:
                pname = Name()
                pname.alt = person_record["name"]['alt']
                pname.type = person_record["name"]['type']
                pname.firstname = person_record["name"]['firstname']
                pname.refname = person_record["name"]['refname']
                pname.surname = person_record["name"]['surname']
                pname.suffix = person_record["name"]['suffix']
                self.name.append(pname)


    @staticmethod       
    def get_person_events (nmax=0, pid=None, names=None):
        """ Voidaan lukea henkilöitä tapahtumineen kannasta seuraavasti:
            get_persons()               kaikki
            get_persons(oid=123)        tietty henkilö oid:n mukaan poimittuna
            get_persons(names='And')    henkilöt, joiden sukunimen alku täsmää
            - lisäksi (nmax=100)         rajaa luettavien henkilöiden määrää
            
        Palauttaa riveillä listan muuttujia:
        n.oid, n.firstname, n.lastname, n.occu, n.place, type(r), events
          0      1            2           3       4      5        6
         146    Bengt       Bengtsson   soldat   null    OSALLISTUI [[...]]    

        jossa 'events' on lista käräjiä, jonka jäseninä on lista ko 
        käräjäin muuttujia:
        [[e.oid, e.kind,  e.name,  e.date,          e.name_orig]...]
            0      1        2        3                4
        [[ 147,  Käräjät, Sakkola, 1669-03-22 … 23, Sakkola 1669.03.22-23]]

        │ Person                       │   │ Name                         │
        ├──────────────────────────────┼───┼──────────────────────────────┤
        │{"gender":"","gramps_handle":"│{} │{"surname":"Andersen","alt":""│
        │handle_6","change":"","id":"6"│   │,"type":"","suffix":"","firstname"│
        │}                             │   │:"Alexander","refname":""}    │
        ├──────────────────────────────┼───┼──────────────────────────────┤
        """
        
        if nmax > 0:
            qmax = "LIMIT " + str(nmax)
        else:
            qmax = ""
        if pid:
            where = "WHERE n.oid={} ".format(pid)
        elif names:
            where = "WHERE n.lastname STARTS WITH '{}' ".format(names)
        else:
            where = ""
#         query = """
#  MATCH (n:Person) {0}
#  OPTIONAL MATCH (n)-[r]->(e) 
#  RETURN n.oid, n.firstname, n.lastname, n.occu, n.place, type(r), 
#   COLLECT([e.oid, e.kind, e.name, e.date, e.name_orig]) AS events
#  ORDER BY n.lastname, n.firstname {1}""".format(where, qmax)

        query = """
 MATCH (n:Person)-->(k:Name) {0}
 OPTIONAL MATCH (n)-[r]->(e) 
 RETURN n.id, k.firstname, k.surname,
  COLLECT([e.name, e.kind]) AS events
 ORDER BY k.surname, k.firstname {1}""".format(where, qmax)
                
        return g.driver.session().run(query)


    @staticmethod       
    def get_person_events2 (uniq_id):
        """ Voidaan lukea henkilöitä tapahtumineen kannasta
        """

        if uniq_id:
            where = "WHERE ID(person)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
 MATCH (person:Person)-->(name:Name) {0}
 OPTIONAL MATCH (person)-[r]->(event:Event)
 OPTIONAL MATCH (event)-[s]->(place:Place)
 RETURN ID(person) AS id, name.firstname AS firstname, 
   name.refname AS refname, name.surname AS surname,
   COLLECT([ID(event), event.type, event.date, place.pname]) AS events
 ORDER BY name.surname, name.firstname""".format(where)
                
        return g.driver.session().run(query)


    def key(self):
        "Hakuavain tuplahenkilöiden löytämiseksi sisäänluvussa"
        key = "{}:{}:{}:{}".format(self.name.firstname, self.name.last, 
              self.occupation, self.place)
        return key

    def join_events(self, events, kind=None):
        """
        Päähenkilöön self yhdistetään tapahtumat listalta events.
        Yhteyden tyyppi on kind, esim. "OSALLISTUI"
        """
        print("**** person.join_events() on toteuttamatta!")
#         eventList = ""
        #Todo: TÄMÄ ON RISA, i:hin EI LAINKAAN VIITATTU
#         for i in events:
#             # Luodaan yhteys (Person)-[:kind]->(Event)
#             for event in self.events:
#                 if event.__class__ != "Event":
#                     raise TypeError("Piti olla Event: {}".format(event.__class__))
# 
#                 # Tapahtuma-noodi
#                 tapahtuma = Node(Event.label, oid=event.oid, kind=event.kind, \
#                         name=event.name, date=event.date)
#                 osallistui = Relationship(persoona, kind, tapahtuma)
#             try:
#                 graph.create(osallistui)
#             except Exception as e:
#                 flash('Lisääminen ei onnistunut: {}. henkilö {}, tapahtuma {}'.\
#                     format(e, persoona, tapahtuma), 'error')
#                 logging.warning('Lisääminen ei onnistunut: {}'.format(e))
#         logging.debug("Yhdistetään henkilöön {} henkilöt {}".format(str(self), eventList))
    
    def join_persons(self, others):
        """
        Päähenkilöön self yhdistetään henkilöiden others tiedot ja tapahtumat
        """
        #TODO Kahden henkilön ja heidän tapahtumiensa yhdistäminen
        othersList = ""
        for i in others:
            othersList.append(str(i) + " ")
        logging.debug("Yhdistetään henkilöön {} henkilöt {}".format(str(self), othersList))
        pass
    
                
                
    @staticmethod
    def get_total():
        """ Tulostaa henkilöiden määrän tietokannassa """
        
        query = """
            MATCH (p:Person) RETURN COUNT(p)
            """
        results =  g.driver.session().run(query)
        
        for result in results:
            return str(result[0])


    def get_points_for_compared_data(self, comp_person, print_out=True):
        """ Tulostaa kahden henkilön tiedot vieretysten """
        points = 0
        print ("*****Person*****")
        if (print_out):
            print ("Handle: " + self.handle + " # " + comp_person.handle)
            print ("Change: " + self.change + " # " + comp_person.change)
            print ("Unique id: " + str(self.uniq_id) + " # " + str(comp_person.uniq_id))
            print ("Id: " + self.id + " # " + comp_person.id)
            print ("Gender: " + self.gender + " # " + comp_person.gender)
        if len(self.name) > 0:
            alt1 = []
            type1 = []
            first1 = []
            refname1 = []
            surname1 = []
            suffix1 = [] 
            alt2 = []
            type2 = []
            first2 = []
            refname2 = [] 
            surname2 = []
            suffix2 = []
            
            names = self.name
            for pname in names:
                alt1.append(pname.alt)
                type1.append(pname.type)
                first1.append(pname.firstname)
                refname1.append(pname.refname)
                surname1.append(pname.surname)
                suffix1.append(pname.suffix)
            
            names2 = comp_person.name
            for pname in names2:
                alt2.append(pname.alt)
                type2.append(pname.type)
                first2.append(pname.firstname)
                refname2.append(pname.refname)
                surname2.append(pname.surname)
                suffix2.append(pname.suffix)
                
            if (len(first2) >= len(first1)):
                for i in range(len(first1)):
                    # Give points if refnames match
                    if refname1[i] != ' ':
                        if refname1[i] == refname2[i]:
                            points += 1
                    if (print_out):
                        print ("Alt: " + alt1[i] + " # " + alt2[i])
                        print ("Type: " + type1[i] + " # " + type2[i])
                        print ("First: " + first1[i] + " # " + first2[i])
                        print ("Refname: " + refname1[i] + " # " + refname2[i])
                        print ("Surname: " + surname1[i] + " # " + surname2[i])
                        print ("Suffix: " + suffix1[i] + " # " + suffix2[i])
            else:
                for i in range(len(first2)):
                    # Give points if refnames match
                    if refname1[i] == refname2[i]:
                        points += 1
                    if (print_out):
                        print ("Alt: " + alt1[i] + " # " + alt2[i])
                        print ("Type: " + type1[i] + " # " + type2[i])
                        print ("First: " + first1[i] + " # " + first2[i])
                        print ("Refname: " + refname1[i] + " # " + refname2[i])
                        print ("Surname: " + surname1[i] + " # " + surname2[i])
                        print ("Suffix: " + suffix1[i] + " # " + suffix2[i])

        return points


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Person*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Gender: " + self.gender)
        print ("Url href: " + self.url_href)
        print ("Url type: " + self.url_type)
        print ("Url description: " + self.url_description)
        if len(self.name) > 0:
            names = self.name
            for pname in names:
                print ("Alt: " + pname.alt)
                print ("Type: " + pname.type)
                print ("First: " + pname.firstname)
                print ("Refname: " + pname.refname)
                print ("Surname: " + pname.surname)
                print ("Suffix: " + pname.suffix)
        if len(self.eventref_hlink) > 0:
            for i in range(len(self.eventref_hlink)):
                print ("Eventref_hlink: " + self.eventref_hlink[i])
                print ("Eventref_role: " + self.eventref_role[i])
        if len(self.parentin_hlink) > 0:
            for i in range(len(self.parentin_hlink)):
                print ("Parentin_hlink: " + self.parentin_hlink[i])
        if len(self.citationref_hlink) > 0:
            for i in range(len(self.citationref_hlink)):
                print ("Citationref_hlink: " + self.citationref_hlink[i])
        return True


    def print_compared_data(self, comp_person, print_out=True):
        """ Tulostaa kahden henkilön tiedot vieretysten """
        points = 0
        print ("*****Person*****")
        if (print_out):
            print ("Handle: " + self.handle + " # " + comp_person.handle)
            print ("Change: " + self.change + " # " + comp_person.change)
            print ("Id: " + self.id + " # " + comp_person.id)
            print ("Gender: " + self.gender + " # " + comp_person.gender)
        if len(self.name) > 0:
            alt1 = []
            type1 = []
            first1 = []
            refname1 = []
            surname1 = []
            suffix1 = [] 
            alt2 = []
            type2 = []
            first2 = []
            refname2 = [] 
            surname2 = []
            suffix2 = []
            
            names = self.name
            for pname in names:
                alt1.append(pname.alt)
                type1.append(pname.type)
                first1.append(pname.firstname)
                refname1.append(pname.refname)
                surname1.append(pname.surname)
                suffix1.append(pname.suffix)
            
            names2 = comp_person.name
            for pname in names2:
                alt2.append(pname.alt)
                type2.append(pname.type)
                first2.append(pname.firstname)
                refname2.append(pname.refname)
                surname2.append(pname.surname)
                suffix2.append(pname.suffix)
                
            if (len(first2) >= len(first1)):
                for i in range(len(first1)):
                    # Give points if refnames match
                    if refname1[i] != ' ':
                        if refname1[i] == refname2[i]:
                            points += 1
                    if (print_out):
                        print ("Alt: " + alt1[i] + " # " + alt2[i])
                        print ("Type: " + type1[i] + " # " + type2[i])
                        print ("First: " + first1[i] + " # " + first2[i])
                        print ("Refname: " + refname1[i] + " # " + refname2[i])
                        print ("Surname: " + surname1[i] + " # " + surname2[i])
                        print ("Suffix: " + suffix1[i] + " # " + suffix2[i])
            else:
                for i in range(len(first2)):
                    # Give points if refnames match
                    if refname1[i] == refname2[i]:
                        points += 1
                    if (print_out):
                        print ("Alt: " + alt1[i] + " # " + alt2[i])
                        print ("Type: " + type1[i] + " # " + type2[i])
                        print ("First: " + first1[i] + " # " + first2[i])
                        print ("Refname: " + refname1[i] + " # " + refname2[i])
                        print ("Surname: " + surname1[i] + " # " + surname2[i])
                        print ("Suffix: " + suffix1[i] + " # " + suffix2[i])

        return points


    def save(self, userid, tx):
        """ Tallettaa henkilön sekä mahdollisesti viitatut nimet, tapahtumat 
            ja sitaatit kantaan 
        """

        today = str(datetime.date.today())
        if not self.handle:
            handles = models.dbutil.get_new_handles(3)
            self.handle = handles.pop()

        # Talleta Person node
        try:
            handle = self.handle
            change = self.change
            pid = self.id
            gender = self.gender
            url_href = self.url_href
            url_type = self.url_type
            url_description = self.url_description
            query = """
CREATE (p:Person) 
SET p.gramps_handle=$handle, 
    p.change=$change, 
    p.id=$id, 
    p.gender=$gender, 
    p.url_href=$url_href, 
    p.url_type=$url_type, 
    p.url_description=$url_description"""
            tx.run(query, 
               {"handle": handle, "change": change, "id": pid, "gender": gender, 
                "url_href": url_href, "url_type": url_type, "url_description": url_description})
        except Exception as err:
            print("Virhe (Person.save:Person): {0}".format(err), file=stderr)

        # Linkitä User nodeen
        try:
            query = """
MATCH (u:User)   WHERE u.userid=$userid
MATCH (n:Person) WHERE n.gramps_handle=$handle
MERGE (u)-[r:REVISION]->(n)
SET r.date=$date"""
            tx.run(query, 
               {"userid": userid, "handle": handle, "date": today})
        except Exception as err:
            print("Virhe (Person.save:User): {0}".format(err), file=stderr)
            
        # Talleta Name nodet ja linkitä henkilöön
        if len(self.name) > 0:
            try:
                names = self.name
                for name in names:
                    p_alt = name.alt
                    p_type = name.type
                    p_firstname = name.firstname
                    p_refname = name.refname
                    p_surname = name.surname
                    p_suffix = name.suffix
                    
                    query = """
CREATE (m:Name) 
SET m.alt=$alt, 
    m.type=$type, 
    m.firstname=$firstname, 
    m.refname=$refname, 
    m.surname=$surname, 
    m.suffix=$suffix
WITH m
MATCH (n:Person) WHERE n.gramps_handle=$handle
MERGE (n)-[r:NAME]->(m)"""
                    tx.run(query, 
                       {"alt": p_alt, "type": p_type, "firstname": p_firstname, 
                        "refname": p_refname, "surname": p_surname, 
                        "suffix": p_suffix, "handle": handle})
            except Exception as err:
                print("Virhe (Person.save:Name): {0}".format(err), file=stderr)

        # Make possible relations to the Event node
        if len(self.events) > 0:
            ''' Create and connect to an Person.event[*] '''
            query = """
MATCH (n:Person) WHERE n.gramps_handle={p_handle}
CREATE (n)-[r:EVENT {role: {role}}]->
      (m:Event {gramps_handle: {e_handle}, id: {e_id},
                name: {e_name}, date: {e_date}, descr: {e_descr}})"""
            for e in self.events:
                if handles:
                    e.handle = handles.pop()
                values = {"p_handle": self.handle,
                          "role": 'osallistuja',
                          "e_handle": e.handle, 
                          "e_id": e.id,
                          "e_name": e.name, # "e_type": e.tyyppi,
                          "e_date": e.date,
                          "e_descr": e.description}
                try:
                    tx.run(query, values)
                except Exception as err:
                    print("Virhe (Person.save:create Event): {0}".format(err), file=stderr)

        elif len(self.eventref_hlink) > 0:
            ''' Connect to an Event loaded form Gramps '''
            for i in range(len(self.eventref_hlink)):
                try:
                    eventref_hlink = self.eventref_hlink[i]
                    query = """
MATCH (n:Person) WHERE n.gramps_handle=$handle
MATCH (m:Event)  WHERE m.gramps_handle=$eventref_hlink
MERGE (n)-[r:EVENT]->(m)"""
                    tx.run(query, 
                       {"handle": handle, "eventref_hlink": eventref_hlink})
                except Exception as err:
                    print("Virhe (Person.save:Event 1): {0}".format(err), file=stderr)

                try:
                    role = self.eventref_role[i]
                    query = """
MATCH (n:Person)-[r:EVENT]->(m:Event)
    WHERE n.gramps_handle=$handle AND m.gramps_handle=$eventref_hlink
SET r.role =$role"""
                    tx.run(query, 
                       {"handle": handle, "eventref_hlink": eventref_hlink, "role": role})
                except Exception as err:
                    print("Virhe (Person.save:Event 2): {0}".format(err), file=stderr)
   
        # Make relations to the Object node
        if len(self.objref_hlink) > 0:
            for i in range(len(self.objref_hlink)):
                try:
                    objref_hlink = self.objref_hlink[i]
                    query = """
MATCH (n:Person)   WHERE n.gramps_handle=$handle
MATCH (m:Object) WHERE m.gramps_handle=$objref_hlink
MERGE (n)-[r:OBJECT]->(m)"""
                    tx.run(query, 
                           {"handle": handle, "objref_hlink": objref_hlink})
                except Exception as err:
                    print("Virhe (Person.save:Object): {0}".format(err), file=stderr)
   
        # Make relations to the Family node
        # This is done in Family.save(), because the Family object is not yet created
#        if len(self.parentin_hlink) > 0:
#            for i in range(len(self.parentin_hlink)):
#                try:
#                    query = """
#                        MATCH (n:Person) WHERE n.gramps_handle='{}'
#                        MATCH (m:Family) WHERE m.gramps_handle='{}'
#                        MERGE (n)-[r:FAMILY]->(m)
#                        """.format(self.handle, self.parentin_hlink[i])
#                    g.driver.session().run(query)
#                except Exception as err:
#                    print("Virhe: {0}".format(err), file=stderr)
   
        # Make relations to the Citation node
        if len(self.citationref_hlink) > 0:
            try:
                citationref_hlink = self.citationref_hlink[0]
                query = """
MATCH (n:Person)   WHERE n.gramps_handle=$handle
MATCH (m:Citation) WHERE m.gramps_handle=$citationref_hlink
MERGE (n)-[r:CITATION]->(m)"""
                tx.run(query, 
                       {"handle": handle, "citationref_hlink": citationref_hlink})
            except Exception as err:
                print("Virhe (Person.save:Citation): {0}".format(err), file=stderr)
#        session.close()
        return


class Name:
    """ Nimi
    
        Properties:
                type            str nimen tyyppi
                alt             str muun nimen numero
                firstname       str etunimi
                refname         str reference name
                surname         str sukunimi
                suffix          str patronyymi
    """
    
    def __init__(self, givn='', surn=''):
        """ Luo uuden name-instanssin """
        self.type = ''
        self.alt = ''
        self.firstname = givn
        self.refname = ''
        self.surname = surn
        self.suffix = ''
        
        
    @staticmethod
    def get_people_with_refname(refname):
        """ Etsi kaikki henkilöt, joiden referenssinimi on annettu"""
        
        query = """
            MATCH (p:Person)-[r:NAME]->(n:Name) WHERE n.refname STARTS WITH '{}'
                RETURN p.gramps_handle AS handle
            """.format(refname)
        return g.driver.session().run(query)

        
    @staticmethod
    def get_people_with_refname_and_user_given(userid, refname):
        """ Etsi kaikki käyttäjän henkilöt, joiden referenssinimi on annettu"""
        
        query = """
            MATCH (u:User)-[r:REVISION]->(p:Person)-[s:NAME]->(n:Name) 
                WHERE u.userid='{}' AND n.refname STARTS WITH '{}'
                RETURN p.gramps_handle AS handle
            """.format(userid, refname)
        return g.driver.session().run(query)

        
    @staticmethod
    def get_ids_of_people_with_refname_and_user_given(userid, refname):
        """ Etsi kaikki käyttäjän henkilöt, joiden referenssinimi on annettu"""
        
        query = """
            MATCH (u:User)-[r:REVISION]->(p:Person)-[s:NAME]->(n:Name) 
                WHERE u.userid='{}' AND n.refname STARTS WITH '{}'
                RETURN ID(p) AS id
            """.format(userid, refname)
        return g.driver.session().run(query)
        
    @staticmethod
    def get_people_with_surname(surname):
        """ Etsi kaikki henkilöt, joiden sukunimi on annettu"""
        
        query = """
            MATCH (p:Person)-[r:NAME]->(n:Name) WHERE n.surname='{}'
                RETURN p.gramps_handle AS handle
            """.format(surname)
        return g.driver.session().run(query)
        
    
    @staticmethod
    def get_all_firstnames():
        """ Listaa kaikki etunimet tietokannassa """
        
        query = """
            MATCH (n:Name) RETURN distinct n.firstname AS firstname
                ORDER BY n.firstname
            """
        return g.driver.session().run(query)
        
    
    @staticmethod
    def get_surnames():
        """ Listaa kaikki sukunimet tietokannassa """
        
        query = """
            MATCH (n:Name) RETURN distinct n.surname AS surname
                ORDER BY n.surname
            """
        return g.driver.session().run(query)
    
    def set_refname(self, tx):
        """Asetetaan etunimen referenssinimi """
        
        query = """
            MATCH (n:Name) WHERE n.firstname='{}' 
            SET n.refname='{}'
            """.format(self.firstname, self.refname)
        return tx.run(query)
