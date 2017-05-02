'''
    Person and Name classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from datetime import date
from sys import stderr


class Person:
    """ Henkilö
            
        Properties:
                handle          
                change
                id                 esim. "I0001"
                gender             str sukupuoli
                name:
                   alt             str muun nimen nro
                   type            str nimen tyyppi
                   first           str etunimi
                   refname         str referenssinimi
                   surname         str sukunimi
                   suffix          str patronyymi
                eventref_hlink     str tapahtuman osoite
                eventref_role      str tapahtuman rooli
                parentin_hlink     str vanhempien osoite
                citationref_hlink  str viittauksen osoite
     """

    def __init__(self):
        """ Luo uuden person-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        self.name = []
        self.eventref_hlink = []
        self.eventref_role = []
        self.parentin_hlink = []
        self.citationref_hlink = []
    
    
    def get_citation_handle(self):
        """ Luetaan henkilön viittauksen handle """
        
        global session
                
        query = """
            MATCH (person:Person)-[r:CITATION]->(c:Citation) 
                WHERE person.gramps_handle='{}'
                RETURN c.gramps_handle AS citationref_hlink
            """.format(self.handle)
        return  session.run(query)
    
    
    def get_event_data(self):
        """ Luetaan henkilön tapahtumien handlet """
        
        global session
                
        query = """
            MATCH (person:Person)-[r:EVENT]->(event:Event) 
                WHERE person.gramps_handle='{}'
                RETURN r.role AS eventref_role, event.gramps_handle AS eventref_hlink
            """.format(self.handle)
        return  session.run(query)
    
    
    def get_her_families(self):
        """ Luetaan naisen perheiden handlet """
        
        global session
                
        query = """
            MATCH (person:Person)<-[r:MOTHER]-(family:Family) 
                WHERE person.gramps_handle='{}'
                RETURN family.gramps_handle AS handle
            """.format(self.handle)
        return  session.run(query)
    
    
    def get_his_families(self):
        """ Luetaan miehen perheiden handlet """
        
        global session
                
        query = """
            MATCH (person:Person)<-[r:FATHER]-(family:Family) 
                WHERE person.gramps_handle='{}'
                RETURN family.gramps_handle AS handle
            """.format(self.handle)
        return  session.run(query)

    
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
    
    
    def get_parentin_handle(self):
        """ Luetaan henkilön perheen handle """
        
        global session
                
        query = """
            MATCH (person:Person)-[r:FAMILY]->(family:Family) 
                WHERE person.gramps_handle='{}'
                RETURN family.gramps_handle AS parentin_hlink
            """.format(self.handle)
        return  session.run(query)
    
    
    def get_person_and_name_data(self):
        """ Luetaan kaikki henkilön tiedot """
        
        global session
                
        query = """
            MATCH (person:Person)-[r:NAME]-(name:Name) 
                WHERE person.gramps_handle='{}'
                RETURN person, name
                ORDER BY name.alt
            """.format(self.handle)
        person_result = session.run(query)
        
        for person_record in person_result:
            self.change = person_record["person"]['change']
            self.id = person_record["person"]['id']
            self.gender = person_record["person"]['gender']
            
            if len(person_record["name"]) > 0:
                pname = Name()
                pname.alt = person_record["name"]['alt']
                pname.type = person_record["name"]['type']
                pname.first = person_record["name"]['first']
                pname.refname = person_record["name"]['refname']
                pname.surname = person_record["name"]['surname']
                pname.suffix = person_record["name"]['suffix']
                self.name.append(pname)
    
    
    def get_person_and_name_data_by_id(self):
        """ Luetaan kaikki henkilön tiedot """
        
        global session
                
        query = """
            MATCH (person:Person)-[r:NAME]-(name:Name) 
                WHERE ID(person)={}
                RETURN person, name
                ORDER BY name.alt
            """.format(self.id)
        person_result = session.run(query)
        
        for person_record in person_result:
            self.change = person_record["person"]['change']
            self.id = person_record["person"]['id']
            self.gender = person_record["person"]['gender']
            
            if len(person_record["name"]) > 0:
                pname = Name()
                pname.alt = person_record["name"]['alt']
                pname.type = person_record["name"]['type']
                pname.first = person_record["name"]['first']
                pname.refname = person_record["name"]['refname']
                pname.surname = person_record["name"]['surname']
                pname.suffix = person_record["name"]['suffix']
                self.name.append(pname)

    def get_person_events (max=0, pid=None, names=None):
        """ Voidaan lukea henkilöitä tapahtumineen kannasta seuraavasti:
            get_persons()               kaikki
            get_persons(oid=123)        tietty henkilö oid:n mukaan poimittuna
            get_persons(names='And')    henkilöt, joiden sukunimen alku täsmää
            - lisäksi (max=100)         rajaa luettavien henkilöiden määrää
            
        Palauttaa riveillä listan muuttujia:
        n.oid, n.firstname, n.lastname, n.occu, n.place, type(r), events
          0      1            2           3       4      5        6
         146    Bengt       Bengtsson   soldat   null    OSALLISTUI [[...]]    

        jossa 'events' on lista käräjiä, jonka jäseninä on lista ko 
        käräjäin muuttujia:
        [[e.oid, e.kind,  e.name,  e.date,          e.name_orig]...]
            0      1        2        3                4
        [[ 147,  Käräjät, Sakkola, 1669-03-22 … 23, Sakkola 1669.03.22-23]]
        """
        global session

        if max > 0:
            qmax = "LIMIT " + str(max)
        else:
            qmax = ""
        if pid:
            where = "WHERE n.oid={} ".format(pid)
        elif names:
            where = "WHERE n.lastname STARTS WITH '{}' ".format(names)
        else:
            where = ""
#       query = """
# MATCH (n:Person) {0}  
# OPTIONAL MATCH (n)-->(e) 
# RETURN n, COLLECT(e)
# ORDER BY n.lastname, n.firstname {1}""".format(where, qmax)
        query = """
 MATCH (n:Person) {0}
 OPTIONAL MATCH (n)-[r]->(e) 
 RETURN n.oid, n.firstname, n.lastname, n.occu, n.place, type(r), 
  COLLECT([e.oid, e.kind, e.name, e.date, e.name_orig]) AS events
 ORDER BY n.lastname, n.firstname {1}""".format(where, qmax)
        return session.run(query)

    def key(self):
        "Hakuavain tuplahenkilöiden löytämiseksi sisäänluvussa"
        key = "{}:{}:{}:{}".format(self.name.first, self.name.last, 
              self.occupation, self.place)
        return key

    def join_events(self, events, kind=None):
        """
        Päähenkilöön self yhdistetään tapahtumat listalta events.
        Yhteyden tyyppi on kind, esim. "OSALLISTUI"
        """
        eventList = ""
        #Todo: TÄMÄ ON RISA, i:hin EI LAINKAAN VIITATTU
        for i in events:
            # Luodaan yhteys (Person)-[:kind]->(Event)
            for event in self.events:
                if event.__class__ != "Event":
                    raise TypeError("Piti olla Event: {}".format(event.__class__))

                # Tapahtuma-noodi
                tapahtuma = Node(Event.label, oid=event.oid, kind=event.kind, \
                        name=event.name, date=event.date)
                osallistui = Relationship(persoona, kind, tapahtuma)
            try:
                graph.create(osallistui)
            except Exception as e:
                flash('Lisääminen ei onnistunut: {}. henkilö {}, tapahtuma {}'.\
                    format(e, persoona, tapahtuma), 'error')
                logging.warning('Lisääminen ei onnistunut: {}'.format(e))
        logging.debug("Yhdistetään henkilöön {} henkilöt {}".format(str(self), eventList))
    
    def join_persons(self, others):
        """
        Päähenkilöön self yhdistetään henkilöiden others tiedot ja tapahtumat
        """
        #TODO Kahden henkilön ja heidän tapahtumiensa yhdistäminen
        othersList = ""
        for i in others:
            otherslist.append(str(i) + " ")
        logging.debug("Yhdistetään henkilöön {} henkilöt {}".format(str(self), othersList))
        pass
    
                
    @staticmethod
    def get_total():
        """ Tulostaa henkilöiden määrän tietokannassa """
        
        global session
                
        query = """
            MATCH (p:Person) RETURN COUNT(p)
            """
        results =  session.run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Person*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Gender: " + self.gender)
        if len(self.name) > 0:
            names = self.name
            for pname in names:
                print ("Alt: " + pname.alt)
                print ("Type: " + pname.type)
                print ("First: " + pname.first)
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
                first1.append(pname.first)
                refname1.append(pname.refname)
                surname1.append(pname.surname)
                suffix1.append(pname.suffix)
            
            names2 = comp_person.name
            for pname in names2:
                alt2.append(pname.alt)
                type2.append(pname.type)
                first2.append(pname.first)
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


    def save(self, userid):
        """ Tallettaa henkilön kantaan """

        global session
        
        today = date.today()
        
        try:
            query = """
                CREATE (p:Person) 
                SET p.gramps_handle='{}', 
                    p.change='{}', 
                    p.id='{}', 
                    p.gender='{}'
                """.format(self.handle, self.change, self.id, self.gender)
                
            session.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            query = """
                MATCH (u:User )WHERE u.userid='{}'
                MATCH (n:Person) WHERE n.gramps_handle='{}'
                MERGE (u)-[r:REVISION]->(n)
                SET r.date='{}'
                """.format(userid, self.handle, today)
                
            session.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
        if len(self.name) > 0:
            try:
                names = self.name
                for name in names:
                    p_alt = name.alt
                    p_type = name.type
                    p_first = name.first
                    p_refname = name.refname
                    p_surname = name.surname
                    p_suffix = name.suffix
                    
                    query = """
                        CREATE (m:Name) 
                        SET m.alt='{}', 
                            m.type='{}', 
                            m.first='{}', 
                            m.refname='{}', 
                            m.surname='{}', 
                            m.suffix='{}'
                        WITH m
                        MATCH (n:Person) WHERE n.gramps_handle='{}'
                        MERGE (n)-[r:NAME]->(m)
                    """.format(p_alt, 
                               p_type, 
                               p_first, 
                               p_refname, 
                               p_surname, 
                               p_suffix, 
                               self.handle)
                
                    session.run(query)
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)

        # Make possible relations to the Event node
        if len(self.eventref_hlink) > 0:
            for i in range(len(self.eventref_hlink)):
                try:
                    query = """
                        MATCH (n:Person) WHERE n.gramps_handle='{}'
                        MATCH (m:Event) WHERE m.gramps_handle='{}'
                        MERGE (n)-[r:EVENT]->(m)
                         """.format(self.handle, self.eventref_hlink[i])
                                 
                    session.run(query)
                except Exception as err:
                    print("Virhe: {0}".format(err), file=stderr)

                try:
                    query = """
                        MATCH (n:Person)-[r:EVENT]->(m:Event)
                            WHERE n.gramps_handle='{}' AND m.gramps_handle='{}'
                        SET r.role ='{}'
                         """.format(self.handle, 
                                    self.eventref_hlink[i], 
                                    self.eventref_role[i])
                                 
                    session.run(query)
                except Exception as err:
                    print("Virhe: {0}".format(err), file=stderr)
   
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
#                                 
#                    session.run(query)
#                except Exception as err:
#                    print("Virhe: {0}".format(err), file=stderr)
   
        # Make relations to the Citation node
        if len(self.citationref_hlink) > 0:
            try:
                query = """
                    MATCH (n:Person) WHERE n.gramps_handle='{}'
                    MATCH (m:Citation) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:CITATION]->(m)
                     """.format(self.handle, self.citationref_hlink[0])
                                 
                session.run(query)
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
        return


class Name:
    """ Nimi
    
        Properties:
                type            str nimen tyyppi
                alt             str muun nimen numero
                first           str etunimi
                refname         str reference name
                surname         str sukunimi
                suffix          str patronyymi
    """
    
    def __init__(self):
        """ Luo uuden name-instanssin """
        self.type = ''
        self.alt = ''
        self.first = ''
        self.refname = ''
        self.surname = ''
        self.suffix = ''
        
        
    @staticmethod
    def get_people_with_refname(refname):
        """ Etsi kaikki henkilöt, joiden referenssinimi on annettu"""
        
        global session
        
        query = """
            MATCH (p:Person)-[r:NAME]->(n:Name) WHERE n.refname STARTS WITH '{}'
                RETURN p.gramps_handle AS handle
            """.format(refname)
        return session.run(query)

        
    @staticmethod
    def get_people_with_refname_and_user_given(userid, refname):
        """ Etsi kaikki käyttäjän henkilöt, joiden referenssinimi on annettu"""
        
        global session
        
        query = """
            MATCH (u:User)-[r:REVISION]->(p:Person)-[s:NAME]->(n:Name) 
                WHERE u.userid='{}' AND n.refname STARTS WITH '{}'
                RETURN p.gramps_handle AS handle
            """.format(userid, refname)
        return session.run(query)

        
    @staticmethod
    def get_ids_of_people_with_refname_and_user_given(userid, refname):
        """ Etsi kaikki käyttäjän henkilöt, joiden referenssinimi on annettu"""
        
        global session
        
        query = """
            MATCH (u:User)-[r:REVISION]->(p:Person)-[s:NAME]->(n:Name) 
                WHERE u.userid='{}' AND n.refname STARTS WITH '{}'
                RETURN ID(p) AS id
            """.format(userid, refname)
        return session.run(query)
        
    @staticmethod
    def get_people_with_surname(surname):
        """ Etsi kaikki henkilöt, joiden sukunimi on annettu"""
        
        global session
        
        query = """
            MATCH (p:Person)-[r:NAME]->(n:Name) WHERE n.surname='{}'
                RETURN p.gramps_handle AS handle
            """.format(surname)
        return session.run(query)
        
    
    @staticmethod
    def get_all_first_names():
        """ Listaa kaikki etunimet tietokannassa """
        
        global session
        
        query = """
            MATCH (n:Name) RETURN distinct n.first AS first
                ORDER BY n.first
            """
        return session.run(query)
        
    
    @staticmethod
    def get_surnames():
        """ Listaa kaikki sukunimet tietokannassa """
        
        global session
        
        query = """
            MATCH (n:Name) RETURN distinct n.surname AS surname
                ORDER BY n.surname
            """
        return session.run(query)
    
    def set_refname(self):
        """Asetetaan etunimen referenssinimi """
        
        global session
        
        query = """
            MATCH (n:Name) WHERE n.first='{}' 
            SET n.refname='{}'
            """.format(self.first, self.refname)
        return session.run(query)
