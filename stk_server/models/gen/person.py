'''
    Person and Name classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

import datetime
from sys import stderr
import logging
#from flask import g
import models.dbutil
import  shareds

class Person:
    """ Henkilö
            
        Properties:
                handle          
                change
                uniq_id            int noden id
                id                 esim. "I0001"
                priv               str merkitty yksityiseksi
                gender             str sukupuoli
                names[]:
                   alt             str muun nimen nro
                   type            str nimen tyyppi
                   firstname       str etunimi
                   refname         str referenssinimi
                   surname         str sukunimi
                   suffix          str patronyymi
                eventref_hlink     str tapahtuman osoite
                eventref_role      str tapahtuman rooli
                objref_hlink       str tallenteen osoite
                urls[]:
                    priv           str url salattu tieto
                    href           str url osoite
                    type           str url tyyppi
                    description    str url kuvaus
                parentin_hlink     str vanhempien osoite
                noteref_hlink      str huomautuksen osoite
                citationref_hlink  str viittauksen osoite
                confidence         str tietojen luotettavuus
                est_birth          str arvioitu syntymäaika
                est_death          str arvioitu kuolinaika
     """

    def __init__(self, pid=''):
        """ Luo uuden person-instanssin """
        self.handle = ''
        self.change = ''
        self.uniq_id = 0
        self.id = pid
        self.names = []
        self.priv = ''
        self.gender = ''
        self.events = []                # For creating display sets
        self.eventref_hlink = []        # Gramps event handles
        self.eventref_role = []
        self.objref_hlink = []
        self.urls = []
        self.parentin_hlink = []
        self.noteref_hlink = []
        self.citationref_hlink = []
        self.confidence = ''
        self.est_birth = ''
        self.est_death = ''
    
    
    def get_citation_id(self):
        """ Luetaan henkilön viittauksen id """
        
        query = """
            MATCH (person:Person)-[r:CITATION]->(c:Citation) 
                WHERE ID(person)={}
                RETURN ID(c) AS citationref_hlink
            """.format(self.uniq_id)
        return  shareds.driver.session().run(query)
    
    
    def get_event_data_by_id(self):
        """ Luetaan henkilön tapahtumien id:t """
        
        pid = int(self.uniq_id)
        query = """
MATCH (person:Person)-[r:EVENT]->(event:Event) 
  WHERE ID(person)=$pid
RETURN r.role AS eventref_role, ID(event) AS eventref_hlink"""
        return  shareds.driver.session().run(query, {"pid": pid})
    
    
    def get_her_families_by_id(self):
        """ Luetaan naisen perheiden id:t """
        
        pid = int(self.uniq_id)
        query = """
MATCH (person:Person)<-[r:MOTHER]-(family:Family) 
  WHERE ID(person)=$pid
RETURN ID(family) AS uniq_id"""
        return  shareds.driver.session().run(query, {"pid": pid})
    
    
    def get_his_families_by_id(self):
        """ Luetaan miehen perheiden id:t """
        
        pid = int(self.uniq_id)
        query = """
MATCH (person:Person)<-[r:FATHER]-(family:Family) 
  WHERE ID(person)=$pid
RETURN ID(family) AS uniq_id"""
        return  shareds.driver.session().run(query, {"pid": pid})

    
    def get_hlinks_by_id(self):
        """ Luetaan henkilön linkit """
            
        event_result = self.get_event_data_by_id()
        for event_record in event_result:            
            self.eventref_hlink.append(event_record["eventref_hlink"])
            self.eventref_role.append(event_record["eventref_role"])

        media_result = self.get_media_id()
        for media_record in media_result:            
            self.objref_hlink.append(media_record["objref_hlink"])

        family_result = self.get_parentin_id()
        for family_record in family_result:            
            self.parentin_hlink.append(family_record["parentin_hlink"])
            
        citation_result = self.get_citation_id()
        for citation_record in citation_result:            
            self.citationref_hlink.append(citation_record["citationref_hlink"])
            
        return True
    
    
    def get_media_id(self):
        """ Luetaan henkilön tallenteen id """
        
        query = """
            MATCH (person:Person)-[r:MEDIA]->(obj:Media) 
                WHERE ID(person)={}
                RETURN ID(obj) AS objref_hlink
            """.format(self.uniq_id)
        return  shareds.driver.session().run(query)
    
    
    def get_parentin_id(self):
        """ Luetaan henkilön syntymäperheen id """
        
        query = """
            MATCH (person:Person)<-[r:CHILD]-(family:Family) 
                WHERE ID(person)={}
                RETURN ID(family) AS parentin_hlink
            """.format(self.uniq_id)
        return  shareds.driver.session().run(query)
    
    
    def get_person_and_name_data_by_id(self):
        """ Luetaan kaikki henkilön tiedot ja nimet
            ╒══════════════════════════════╤══════════════════════════════╕
            │"person"                      │"name"                        │
            ╞══════════════════════════════╪══════════════════════════════╡
            │{"gender":"F","url_type":[],"c│{"firstname":"Margareta Elisab│
            │hange":"1507492602","gramps_ha│et","surname":"Enckell","alt":│
            │ndle":"_d9ea5e7f9a00a0482af","│"","type":"Birth Name","suffix│
            │id":"I0098","url_href":[],"url│":"","refname":"Margareta Elis│
            │_description":[]}             │abeth/Enckell/"}              │
            ├──────────────────────────────┼──────────────────────────────┤
            │{"gender":"F","url_type":[],"c│{"firstname":"Margareta","surn│
            │hange":"1507492602","gramps_ha│ame":"Utter","alt":"1","type":│
            │ndle":"_d9ea5e7f9a00a0482af","│"Married Name","suffix":"","re│
            │id":"I0098","url_href":[],"url│fname":"Margareta/Utter/"}    │
            │_description":[]}             │                              │
            └──────────────────────────────┴──────────────────────────────┘
        """
        pid = int(self.uniq_id)
        query = """
MATCH (person:Person)-[r:NAME]->(name:Name) 
  WHERE ID(person)=$pid
RETURN person, name
  ORDER BY name.alt"""
        person_result = shareds.driver.session().run(query, {"pid": pid})
        self.id = None
        
        for person_record in person_result:
            if self.id == None:
                self.handle = person_record["person"]['handle']
                self.change = person_record["person"]['change']
                self.id = person_record["person"]['id']
                self.priv = person_record["person"]['priv']
                self.gender = person_record["person"]['gender']
                self.confidence = person_record["person"]['confidence']
                self.est_birth = person_record["person"]['est_birth']
                self.est_death = person_record["person"]['est_death']
            
            if len(person_record["name"]) > 0:
                pname = Name()
                pname.alt = person_record["name"]['alt']
                pname.type = person_record["name"]['type']
                pname.firstname = person_record["name"]['firstname']
                pname.refname = person_record["name"]['refname']
                pname.surname = person_record["name"]['surname']
                pname.suffix = person_record["name"]['suffix']
                self.names.append(pname)
                

    def get_person_w_names(self):
        """ Luetaan kaikki henkilön tiedot ja nimet
            ╒══════════════════════════════╤══════════════════════════════╕
            │"person"                      │"names"                       │
            ╞══════════════════════════════╪══════════════════════════════╡
            │{"gender":"F","url_type":[],"c│[{"firstname":"Margareta Elisa│
            │hange":"1507492602","gramps_ha│bet","surname":"Enckell","alt"│
            │ndle":"_d9ea5e7f9a00a0482af","│:"","type":"Birth Name","suffi│
            │id":"I0098","url_href":[],"url│x":"","refname":"Margareta Eli│
            │_description":[]}             │sabeth/Enckell/"},            │
            │                              │                  {"firstname"│
            │                              │:"Margareta","surname":"Utter"│
            │                              │,"alt":"1","type":"Married Nam│
            │                              │e","suffix":"","refname":"Marg│
            │                              │areta/Utter/"}]               │
            └──────────────────────────────┴──────────────────────────────┘        """
#         query = """
# MATCH (person:Person)-[r:NAME]-(name:Name) 
#   WHERE ID(person)=$pid
# RETURN person, name
#   ORDER BY name.alt"""
        query = """
MATCH (person:Person)-[r:NAME]->(name:Name) 
  WHERE ID(person)=$pid
OPTIONAL MATCH (person)-[wu:WEBURL]->(weburl:Weburl)
  WITH person, name, COLLECT (weburl) AS urls ORDER BY name.alt
RETURN person, urls, COLLECT (name) AS names
        """
        person_result = shareds.driver.session().run(query, pid=int(self.uniq_id))
        
        for person_record in person_result:
            self.handle = person_record["person"]['handle']
            self.change = person_record["person"]['change']
            self.id = person_record["person"]['id']
            self.priv = person_record["person"]['priv']
            self.gender = person_record["person"]['gender']
            self.confidence = person_record["person"]['confidence']
            self.est_birth = person_record["person"]['est_birth']
            self.est_death = person_record["person"]['est_death']
            
            for name in person_record["names"]:
                pname = Name()
                pname.alt = name['alt']
                pname.type = name['type']
                pname.firstname = name['firstname']
                pname.refname = name['refname']
                pname.surname = name['surname']
                pname.suffix = name['suffix']
                self.names.append(pname)
            
            for url in person_record["urls"]:
                weburl = Weburl()
                weburl.priv = url['priv']
                weburl.href = url['href']
                weburl.type = url['type']
                weburl.description = url['description']
                self.urls.append(weburl)
        
        
    @staticmethod
    def get_people_with_same_birthday():
        """ Etsi kaikki henkilöt, joiden syntymäaika on sama"""
        
        query = """
            MATCH (p1:Person)-[r1:NAME]->(n1:Name) WHERE p1.est_birth<>''
            MATCH (p2:Person)-[r2:NAME]->(n2:Name) WHERE ID(p1)<ID(p2) AND
                p2.gender = p1.gender AND p2.est_birth = p1.est_birth
                RETURN COLLECT ([ID(p1), p1.est_birth, p1.est_death, n1.firstname, n1.surname, 
                ID(p2), p2.est_birth, p2.est_death, n2.firstname, n2.surname]) AS ids
            """.format()
        return shareds.driver.session().run(query)
        
        
    @staticmethod
    def get_people_with_same_deathday():
        """ Etsi kaikki henkilöt, joiden kuolinaika on sama"""
        
        query = """
            MATCH (p1:Person)-[r1:NAME]->(n1:Name) WHERE p1.est_death<>''
            MATCH (p2:Person)-[r2:NAME]->(n2:Name) WHERE ID(p1)<ID(p2) AND
                p2.gender = p1.gender AND p2.est_death = p1.est_death
                RETURN COLLECT ([ID(p1), p1.est_birth, p1.est_death, n1.firstname, n1.surname, 
                ID(p2), p2.est_birth, p2.est_death, n2.firstname, n2.surname]) AS ids
            """.format()
        return shareds.driver.session().run(query)


    @staticmethod       
    def get_people_wo_birth():
        """ Voidaan lukea henkilöitä ilman syntymätapahtumaa kannasta
        """
        
        query = """
 MATCH (p:Person) WHERE NOT EXISTS ((p)-[:EVENT]->(:Event {type:'Birth'}))
 WITH p 
 MATCH (p)-[:NAME]->(n:Name)
 RETURN ID(p) AS uniq_id, p, n ORDER BY n.surname, n.firstname"""
                
        result = shareds.driver.session().run(query)
        
        titles = ['uniq_id', 'gramps_handle', 'change', 'id', 'priv', 'gender',
                  'firstname', 'surname']
        lists = []
        
        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["p"]['gramps_handle']:
                data_line.append(record["p"]['gramps_handle'])
            else:
                data_line.append('-')
            if record["p"]['change']:
                data_line.append(record["p"]['change'])
            else:
                data_line.append('-')
            if record["p"]['id']:
                data_line.append(record["p"]['id'])
            else:
                data_line.append('-')
            if record["p"]['priv']:
                data_line.append(record["p"]['priv'])
            else:
                data_line.append('-')
            if record["p"]['gender']:
                data_line.append(record["p"]['gender'])
            else:
                data_line.append('-')
            if record["n"]['firstname']:
                data_line.append(record["n"]['firstname'])
            else:
                data_line.append('-')
            if record["n"]['surname']:
                data_line.append(record["n"]['surname'])
            else:
                data_line.append('-')
                
            lists.append(data_line)
        
        return (titles, lists)
    
    
    @staticmethod       
    def get_old_people_top():
        """ Voidaan lukea henkilöitä joilla syntymä- ja kuolintapahtumaa kannasta
        """
        
        query = """
 MATCH (p:Person)-[:EVENT]->(a:Event) WHERE EXISTS ((p)-[:EVENT]->(a:Event {type:'Birth'}))
 WITH p, a 
 MATCH (p)-[:EVENT]->(b:Event) WHERE EXISTS ((p)-[:EVENT]->(b:Event {type:'Death'}))
 WITH p, a, b
 MATCH (p)-[:NAME]->(n:Name)
 RETURN ID(p) AS uniq_id, p, n, a.date AS birth, b.date AS death ORDER BY n.surname, n.firstname"""
                
        result = shareds.driver.session().run(query)
        
        titles = ['uniq_id', 'firstname', 'surname', 'birth', 'death', 
                  'age (years)', 'age (months)', 'age(12*years + months)']
        lists = []
        
        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["n"]['firstname']:
                data_line.append(record["n"]['firstname'])
            else:
                data_line.append('-')
            if record["n"]['surname']:
                data_line.append(record["n"]['surname'])
            else:
                data_line.append('-')
            if record['birth']:
                birth_str = record['birth']
                birth_data = birth_str.split("-")
                data_line.append(record['birth'])
            else:
                data_line.append('-')
            if record['death']:
                death_str = record['death']
                death_data = death_str.split("-")
                data_line.append(record['death'])
            else:
                data_line.append('-')
                
            # Counting the age when the dates are as YYYY-mm-dd
            if (len(birth_data) > 2) and (len(death_data) > 2):
                years = int(death_data[0])-int(birth_data[0])
                months = int(death_data[1])-int(birth_data[1])
                
                if int(death_data[2]) < int(death_data[2]):
                    months -= 1
                
                if months < 0:
                    months += 12
                    years -= 1
                
                years_months = years * 12 + months
            else:
                years = '-'
                months = '-'
                years_months = 0
                
            data_line.append(years)
            data_line.append(months)
            data_line.append(years_months)

                
            lists.append(data_line)
        
        return (titles, lists)


    @staticmethod       
    def get_confidence ():
        """ Voidaan lukea henkilön tapahtumien luotettavuustiedot kannasta
        """

        query = """
 MATCH (person:Person)
 OPTIONAL MATCH (person)-[:EVENT]->(event:Event)-[r:CITATION]->(c:Citation)
 RETURN ID(person) AS uniq_id, COLLECT(c.confidence) AS list"""
                
        return shareds.driver.session().run(query)


    def set_confidence (self, tx):
        """ Voidaan asettaa henkilön tietojen luotettavuus arvio kantaan
        """

        query = """
 MATCH (person:Person) WHERE ID(person)={}
 SET person.confidence='{}'""".format(self.uniq_id, self.confidence)
                
        return shareds.driver.session().run(query)


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
 MATCH (n:Person)-[:NAME]->(k:Name) {0}
 OPTIONAL MATCH (n)-[r:EVENT]->(e) 
 RETURN n.id, k.firstname, k.surname,
  COLLECT([e.name, e.kind]) AS events
 ORDER BY k.surname, k.firstname {1}""".format(where, qmax)
                
        return shareds.driver.session().run(query)


    @staticmethod       
    def get_events_k (keys):
        """ Voidaan lukea henkilöitä tapahtumineen kannasta
            a) Tietokanta-avaimella valittu henkilö
            b) nimellä poimittu henkilö
               rule='all'       kaikki
               rule='surname'   sukunimen alkuosalla
               rule='firstname' etunimen alkuosalla
               rule='suffix'    patronyymin alkuosalla
        """
        if keys:
            rule=keys[0]
            name=keys[1] if len(keys) > 1 else None
            print("Rajaus {} '{}'".format(rule, name))
        else:
            rule="all"
            name=""

# ╒═══════╤══════╤══════╤═════╤═════════╤══════════╤══════════════════════════════╕
# │"id"   │"confi│"first│"ref │"surname"│"suffix"  │"events"                      │
# │       │dence"│name" │name"│         │          │                              │
# ╞═══════╪══════╪══════╪═════╪═════════╪══════════╪══════════════════════════════╡
# │"27204"│null  │"Henri│""   │"Sibbe"  │"Mattsson"│[["26836","Occupation","","","│
# │       │      │k"    │     │         │          │","","Cappelby 4 Sibbes"],["26│
# │       │      │      │     │         │          │255","Birth","1709-01-03","","│
# │       │      │      │     │         │          │","",null],["26837","Luottamus│
# │       │      │      │     │         │          │toimi","1760","","","",null]] │
# ├───────┼──────┼──────┼─────┼─────────┼──────────┼──────────────────────────────┤
        qend="""
 OPTIONAL MATCH (person)-[:EVENT]->(event:Event)
 OPTIONAL MATCH (event)-[:EVENT]->(place:Place)
RETURN ID(person) AS id, person.confidence AS confidence, 
    person.est_birth AS est_birth, person.est_death AS est_death,
    name.firstname AS firstname, 
    name.refname AS refname, name.surname AS surname, 
    name.suffix AS suffix,
    COLLECT([ID(event), event.type, event.date, event.datetype, 
        event.daterange_start, event.daterange_stop, place.pname]) AS events
ORDER BY name.surname, name.firstname"""

        if rule == "uniq_id":
            # Person selected by uniq_id
            query = "MATCH (person:Person)-[:NAME]->(name:Name) WHERE ID(person)=$id" + qend
            return shareds.driver.session().run(query, id=int(name))
        if rule == 'all':
            query = "MATCH (person:Person)-[:NAME]->(name:Name)" + qend
            return shareds.driver.session().run(query)
        if rule == "surname":
            query = "MATCH (person:Person)-[:NAME]->(name:Name) WHERE name.surname STARTS WITH $id" + qend
        elif rule == "firstname":
            query = "MATCH (person:Person)-[:NAME]->(name:Name) WHERE name.firstname STARTS WITH $id" + qend
        elif rule == "suffix":
            query = "MATCH (person:Person)-[:NAME]->(name:Name) WHERE name.suffix STARTS WITH $id" + qend
        else:
            print ("Tätä rajausta ei ole vielä tehty: " + rule)
            return None
        # All with string argument
        return shareds.driver.session().run(query, id=name)


    @staticmethod       
    def get_family_members (uniq_id):
        """ Read person's families and family members for Person page
        """

        query="""
MATCH (p:Person)<--(f:Family)-[r]->(m:Person)-[:NAME]->(n:Name) WHERE ID(p) = $id
    OPTIONAL MATCH (m)-[:EVENT]->(birth {type:'Birth'})
    WITH f.id AS family_id, ID(f) AS f_uniq_id, 
        TYPE(r) AS role, m.id AS m_id, ID(m) AS uniq_id, 
        m.gender AS gender, birth.date AS birth_date, 
        n.alt AS alt, n.type AS ntype, n.firstname AS fn, n.surname AS sn, n.suffix AS sx
    ORDER BY n.alt
    RETURN family_id, f_uniq_id, role, m_id, uniq_id, gender, birth_date,
        COLLECT([alt, ntype, fn, sn, sx]) AS names
    ORDER BY family_id, role, birth_date
UNION 
MATCH (p:Person)<-[l]-(f:Family) WHERE id(p) = $id
    RETURN f.id AS family_id, ID(f) AS f_uniq_id, TYPE(l) AS role, p.id AS m_id, ID(p) AS uniq_id, 
        p.gender AS gender, "" AS birth_date, [] AS names"""

# ╒═══════════╤═══════════╤════════╤═══════╤═════════╤════════╤════════════╤══════════════════════════════╕
# │"family_id"│"f_uniq_id"│"role"  │"m_id" │"uniq_id"│"gender"│"birth_date"│"names"                       │
# ╞═══════════╪═══════════╪════════╪═══════╪═════════╪════════╪════════════╪══════════════════════════════╡
# │"F0012"    │"40506"    │"CHILD" │"27044"│"27044"  │"M"     │"1869-03-28"│[["","Birth Name","Christian",│
# │           │           │        │       │         │        │            │"Sibelius",""],["1","Also Know│
# │           │           │        │       │         │        │            │n As","Kristian","Sibelius",""│
# │           │           │        │       │         │        │            │]]                            │
# ├───────────┼───────────┼────────┼───────┼─────────┼────────┼────────────┼──────────────────────────────┤

        return shareds.driver.session().run(query, id=int(uniq_id))
    

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
        results =  shareds.driver.session().run(query)
        
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
            print ("Priv: " + self.priv + " # " + comp_person.priv)
            print ("Gender: " + self.gender + " # " + comp_person.gender)
        if len(self.names) > 0:
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
            
            names = self.names
            for pname in names:
                alt1.append(pname.alt)
                type1.append(pname.type)
                first1.append(pname.firstname)
                refname1.append(pname.refname)
                surname1.append(pname.surname)
                suffix1.append(pname.suffix)
            
            names2 = comp_person.names
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


    @staticmethod
    def set_estimated_dates():
        # Set est_birth
        try:
            dtype = 'Birth'
            query = """
MATCH (n:Person)-[r:EVENT]->(m:Event)
    WHERE m.type=$type
SET r.type =$type
SET n.est_birth = m.daterange_start"""
            result = shareds.driver.session().run(query, 
               {"type": dtype})
            counters = result.consume().counters
            msg = "Muutettu {} est_birth-tietoa".format(counters.properties_set)
        except Exception as err:
            print("Virhe (Person.save:est_birth): {0}".format(err), file=stderr)
            
        # Set est_birth
        try:
            dtype = 'Death'
            query = """
MATCH (n:Person)-[r:EVENT]->(m:Event)
    WHERE m.type=$type
SET r.type =$type
SET n.est_death = m.daterange_start"""
            result = shareds.driver.session().run(query, 
               {"type": dtype})
            counters = result.consume().counters
            msg = msg + " ja {} est_death-tietoa.".format(counters.properties_set)
            return msg
        except Exception as err:
            print("Virhe (Person.save:est_death): {0}".format(err), file=stderr)
        

    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Person*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Priv: " + self.priv)
        print ("Gender: " + self.gender)

        if len(self.names) > 0:
            for pname in self.names:
                print ("Alt: " + pname.alt)
                print ("Type: " + pname.type)
                print ("First: " + pname.firstname)
                print ("Refname: " + pname.refname)
                print ("Surname: " + pname.surname)
                print ("Suffix: " + pname.suffix)
            
        if len(self.urls) > 0:
            for url in self.urls:
                print ("Url priv: " + url.priv)
                print ("Url href: " + url.href)
                print ("Url type: " + url.type)
                print ("Url description: " + url.description)
                
        if len(self.eventref_hlink) > 0:
            for i in range(len(self.eventref_hlink)):
                print ("Eventref_hlink: " + self.eventref_hlink[i])
                print ("Eventref_role: " + self.eventref_role[i])
        if len(self.parentin_hlink) > 0:
            for i in range(len(self.parentin_hlink)):
                print ("Parentin_hlink: " + self.parentin_hlink[i])
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                print ("Noteref_hlink: " + self.noteref_hlink[i])
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
            print ("Priv: " + self.priv + " # " + comp_person.priv)
            print ("Gender: " + self.gender + " # " + comp_person.gender)
        if len(self.names) > 0:
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
            
            names = self.names
            for pname in names:
                alt1.append(pname.alt)
                type1.append(pname.type)
                first1.append(pname.firstname)
                refname1.append(pname.refname)
                surname1.append(pname.surname)
                suffix1.append(pname.suffix)
            
            names2 = comp_person.names
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


    def save(self, username, tx):
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
            priv = self.priv
            gender = self.gender
            query = """
CREATE (p:Person) 
SET p.gramps_handle=$handle, 
    p.change=$change, 
    p.id=$id, 
    p.priv=$priv, 
    p.gender=$gender"""
            tx.run(query, 
               {"handle": handle, "change": change, "id": pid, "priv": priv, "gender": gender})
            
        except Exception as err:
            print("Virhe (Person.save:Person): {0}".format(err), file=stderr)

        # Linkitä User nodeen
        try:
            query = """
MATCH (u:UserProfile) WHERE u.userName=$username
MATCH (n:Person) WHERE n.gramps_handle=$handle
MERGE (u)-[r:REVISION]->(n)
SET r.date=$date"""
            tx.run(query, 
               {"username": username, "handle": handle, "date": today})
        except Exception as err:
            print("Virhe (Person.save:User): {0}".format(err), file=stderr)
            
        # Talleta Name nodet ja linkitä henkilöön
        if len(self.names) > 0:
            try:
                names = self.names
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
            
        # Talleta Weburl nodet ja linkitä henkilöön
        if len(self.urls) > 0:
            for url in self.urls:
                url_priv = url.priv
                url_href = url.href
                url_type = url.type
                url_description = url.description
                query = """
MATCH (n:Person) WHERE n.gramps_handle=$handle
CREATE (n)-[wu:WEBURL]->
      (url:Weburl {priv: {url_priv}, href: {url_href},
                type: {url_type}, description: {url_description}})"""
                try:
                    tx.run(query, 
                           {"handle": handle, "url_priv": url_priv, "url_href": url_href,
                            "url_type":url_type, "url_description":url_description})
                except Exception as err:
                    print("Virhe (Person.save:create Weburl): {0}".format(err), file=stderr)

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
   
        # Make relations to the Media node
        if len(self.objref_hlink) > 0:
            for i in range(len(self.objref_hlink)):
                try:
                    objref_hlink = self.objref_hlink[i]
                    query = """
MATCH (n:Person)   WHERE n.gramps_handle=$handle
MATCH (m:Media) WHERE m.gramps_handle=$objref_hlink
MERGE (n)-[r:MEDIA]->(m)"""
                    tx.run(query, 
                           {"handle": handle, "objref_hlink": objref_hlink})
                except Exception as err:
                    print("Virhe (Person.save:Media): {0}".format(err), file=stderr)
   
        # Make relations to the Family node will be done in Family.save(),
        # because the Family object is not yet created
   
        # Make relations to the Note node
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                try:
                    noteref_hlink = self.noteref_hlink[i]
                    query = """
MATCH (n:Person)   WHERE n.gramps_handle=$handle
MATCH (m:Note) WHERE m.gramps_handle=$noteref_hlink
MERGE (n)-[r:NOTE]->(m)"""
                    tx.run(query, 
                           {"handle": handle, "noteref_hlink": noteref_hlink})
                except Exception as err:
                    print("Virhe (Person.save:Note): {0}".format(err), file=stderr)
   
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


class Person_as_member(Person):
    """ A person as a family member 

        Extra properties:
            role         str "CHILD", "FATHER" or "MOTHER"
            birth_date   str (TODO: Should be DateRange)
     """

    def __init__(self):
        """ Luo uuden instanssin """
        Person.__init__(self)
        self.role = ''
        self.birth_date = ''


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
    
    def __init__(self, givn='', surn='', suff=''):
        """ Luo uuden name-instanssin """
        self.type = ''
        self.alt = ''
        self.firstname = givn
        self.refname = ''
        self.surname = surn
        self.suffix = suff
        
        
    @staticmethod
    def get_people_with_refname(refname):
        """ Etsi kaikki henkilöt, joiden referenssinimi on annettu"""
        
        query = """
            MATCH (p:Person)-[r:NAME]->(n:Name) WHERE n.refname STARTS WITH '{}'
                RETURN p.gramps_handle AS handle
            """.format(refname)
        return shareds.driver.session().run(query)
        
        
    @staticmethod
    def get_people_with_same_name():
        """ Etsi kaikki henkilöt, joiden nimi on sama"""
        
        query = """
            MATCH (p1:Person)-[r1:NAME]->(n1:Name)
            MATCH (p2:Person)-[r2:NAME]->(n2:Name) WHERE ID(p1)<ID(p2)
                AND n2.surname = n1.surname AND n2.firstname = n1.firstname
                RETURN COLLECT ([ID(p1), p1.est_birth, p1.est_death, n1.firstname, n1.surname, 
                ID(p2), p2.est_birth, p2.est_death, n2.firstname, n2.surname]) AS ids
            """.format()
        return shareds.driver.session().run(query)

        
    @staticmethod
    def get_ids_of_people_with_refname_and_user_given(userid, refname):
        """ Etsi kaikki käyttäjän henkilöt, joiden referenssinimi on annettu"""
        
        query = """
            MATCH (u:User)-[r:REVISION]->(p:Person)-[s:NAME]->(n:Name) 
                WHERE u.userid='{}' AND n.refname STARTS WITH '{}'
                RETURN ID(p) AS id
            """.format(userid, refname)
        return shareds.driver.session().run(query)
        
    @staticmethod
    def get_people_with_surname(surname):
        """ Etsi kaikki henkilöt, joiden sukunimi on annettu"""
        
        query = """
            MATCH (p:Person)-[r:NAME]->(n:Name) WHERE n.surname='{}'
                RETURN DISTINCT ID(p) AS uniq_id
            """.format(surname)
        return shareds.driver.session().run(query)
        
    
    @staticmethod
    def get_all_firstnames():
        """ Poimii kaikki henkilöiden Name:t etunimijärjestyksessä 
╒═══════╤══════════════════════╤════════════╤═════════╤══════════════════════════════╤═════╕
│"ID"   │"fn"                  │"sn"        │"pn"     │"rn"                          │"sex"│
╞═══════╪══════════════════════╪════════════╪═════════╪══════════════════════════════╪═════╡
│"30691"│"Abraham"             │"Palander"  │""       │"Aappo/Palander/"             │"M"  │
├───────┼──────────────────────┼────────────┼─────────┼──────────────────────────────┼─────┤
│"30786"│"Abraham Mathias"     │"Bruncrona" │""       │"Aappo Mathias/Bruncrona/"    │"M"  │
├───────┼──────────────────────┼────────────┼─────────┼──────────────────────────────┼─────┤
│"30950"│"Adolf Mathias Israel"│"Sucksdorff"│""       │"Adolf Mathias Israel/Sucksdor│"M"  │
│       │                      │            │         │ff/"                          │     │
├───────┼──────────────────────┼────────────┼─────────┼──────────────────────────────┼─────┤
│"30281"│"Agata Eufrosine"     │"Tolpo"     │"Gabriels│"Agaata Eufrosine/Tolpo/"     │"F"  │
│       │                      │            │dotter"  │                              │     │
└───────┴──────────────────────┴────────────┴─────────┴──────────────────────────────┴─────┘
        TODO: sex-kenttää ei nyt käytetä, keventäisi jättää pois
        """
        
        query = """
MATCH (n)<-[r:NAME]-(a) 
RETURN ID(n) AS ID, n.firstname AS fn, 
       n.surname AS sn, n.suffix AS pn, n.refname as rn,
       a.gender AS sex
ORDER BY n.firstname"""
        return shareds.driver.session().run(query)
        
    
    @staticmethod
    def get_surnames():
        """ Listaa kaikki sukunimet tietokannassa """
        
        query = """
            MATCH (n:Name) RETURN distinct n.surname AS surname
                ORDER BY n.surname
            """
        return shareds.driver.session().run(query)


    @staticmethod
    def set_refname(tx, uniq_id, refname):
        """Asetetaan etunimen referenssinimi  """
        
        query = """
MATCH (n:Name) WHERE ID(n)=$id
SET n.refname=$refname
            """
        return tx.run(query, id=uniq_id, refname=refname)
    
    
class Weburl:
    '''
    Netti URL
    
        Properties:
                url_priv           str url salattu tieto
                url_href           str url osoite
                url_type           str url tyyppi
                url_description    str url kuvaus
    '''

    def __init__(self):
        """ Luo uuden weburl-instanssin """
        self.priv = ''
        self.href = ''
        self.type = ''
        self.description = ''

    def __str__(self):
        desc = "Weburl ({}) '{}'-->'{}'".format(self.type, self.description, self.href)
        return desc

