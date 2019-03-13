'''
    Person compound includes operations for accessing
    - Person and her Names
    - related Events and Places
    
    Note. Use classmethod models.gen.person.Person.from_node(node) to create 
        a Person_combo instance from a db node
        or models.gen.person_combo.Person_combo.__init__() for empty instance

    class gen.person_combo.Person_combo(Person): 
        - __init__()
        - get_person_w_names(self)      Luetaan kaikki henkilön tiedot ja nimet
        - get_people_with_same_birthday() Etsi henkilöt, joiden syntymäaika on sama
        - get_people_with_same_deathday() Etsi henkilöt, joiden kuolinaika on sama
        - get_people_wo_birth()         Luetaan henkilöt ilman syntymätapahtumaa
        - get_old_people_top()          Henkilöt joilla syntymä- ja kuolintapahtuma
        - get_person_events (nmax=0, pid=None, names=None)
                                        Luetaan henkilöitä tapahtumineen
        - get_person_combos (keys, currentuser, take_refnames=False, order=0):
                                        Read Persons with Names, Events and Refnames
        - get_my_places(self)              Tallettaa liittyvät Paikat henkilöön
        - get_all_citation_source(self) Tallettaa liittyvät Cition ja Source
        - get_all_notes(self)           Tallettaa liittyvät Notes (ja web-viittaukset)
        - get_family_members (uniq_id)  Luetaan liittyvät Names, Families and Events
        - get_refnames(pid)             Luetaan liittyvät Refnames
        # save(self, username, tx)      see: bp.gramps.models.person_gramps.Person_gramps.save

    Not in use or obsolete:
        - get_citation_id(self)         Luetaan henkilöön liittyvän viittauksen id
        - get_event_data_by_id(self)    Luetaan henkilön tapahtumien id:t
        - get_her_families_by_id(self)  Luetaan naisen perheiden id:t
        - get_his_families_by_id(self)  Luetaan miehen perheiden id:t
        - get_hlinks_by_id(self)        Luetaan henkilön linkit (_hlink)
        - get_media_id(self)            Luetaan henkilön tallenteen id
        - get_parentin_id(self)         Luetaan henkilön syntymäperheen id
        - get_person_and_name_data_by_id(self)
                                        Luetaan kaikki henkilön tiedot ja nimet
        - get_points_for_compared_data(self, comp_person, print_out=True)
                                        Tulostaa kahden henkilön tiedot vieretysten
        - print_compared_data(self, comp_person, print_out=True) 
                                        Tulostaa kahden henkilön tiedot vieretysten

        # set_estimated_life()          Aseta est_birth ja est_death
        - save()  see: bp.gramps.models.person_gramps.Person_gramps.save


@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi> & Juha Mäkeläinen
'''

from sys import stderr

import shareds
from .person import Person
from .person_name import Name
from .event_combo import Event_combo
from .cypher import Cypher_person, Cypher_family
from .place import Place, Place_name
from .dates import DateRange
#from models.owner import OwnerFilter


class Person_combo(Person):
    """ A Person combined from database person node, names, events etc.
    
        From Person.__init__(): 
            uniq_id, handle, id, priv, sex, confidence, lifetime, change
            Obsolete: #est_birth, #est_death

        Other properties:
            names[]:
               order           int index of name variations; number 0 is default name
               #alt            str muun nimen nro
               type            str nimen tyyppi
               firstname       str etunimi
               surname         str sukunimi
               suffix          str patronyymi
            confidence         str tietojen luotettavuus

        The indexes of referred objects are in variables:
            eventref_hlink[]   int tapahtuman uniq_id, rooli 
            - eventref_role[]  str edellisen rooli
            media_ref[]        int median uniq_id (previous objref_hlink[])
            parentin_hlink[]   int vanhempien uniq_id
            noteref_hlink[]    int huomautuksen uniq_id tai handle?
            citation_ref[]     int viittauksen uniq_id    (ent.citationref_hlink)
     """

    def __init__(self):
        """ Create a Person instance. 
        """
        Person.__init__(self)

        # For embadded or referenced child objects, displaying Person page
        # @see Plan bp.scene.data_reader.connect_object_as_leaf

        self.names = []                 # models.gen.person_name.Name

        self.events = []                # models.gen.event_combo.Event_combo
        self.event_ref = []             # Event uniq_ids # Gramps event handles (?)
        self.eventref_role = []         # ... and roles

        self.citation_ref = []          # models.gen.citation.Citation
        #remove: self.citations = []
        self.note_ref = []              # uniq_id of models.gen.note.Note
        self.notes = []                 # 
        #remove: self.noteref_hlink = []

        self.media_ref = []             # uniq_id of models.gen.media.Media
                                        # (previous self.objref_hlink[])

        # Other variables

        #self.urls = []                # REMOVED: Now use note_ref[]
        self.est_birth = ''
        self.est_death = ''

        self.families_as_child = []     # - Propably one only
        self.families_as_parent =[]
        self.parentin_hlink = []


    @staticmethod
    def get_person_paths(uniq_id):
        ''' Read a person and paths for all connected nodes.
        '''
        query = """
match path = (p) -[*]-> (x)
    where id(p) = $pid 
return path"""
#         query2="""
# match path = (p) -[*]-> () where id(p) = $pid 
#     with p, relationships(path) as rel
# return extract(x IN rel | [id(startnode(x)), type(x), x.role, endnode(x)]) as relations"""
        return  shareds.driver.session().run(query, pid=uniq_id)

    @staticmethod
    def get_person_paths_apoc(uniq_id):
        ''' Read a person and paths for all connected nodes.
        '''
        try:
            return  shareds.driver.session().run(Cypher_person.all_nodes_query_w_apoc, 
                                                 pid=uniq_id)
        except Exception as e:
            print("Henkilötietojen {} luku epäonnistui: {} {}".format(uniq_id, e.__class__().name, e))
            return None

    @staticmethod
    def read_my_persons_list(o_filter, limit=100):
        """ Reads Person Name and Event objects for display.

            By default, 100 names are got beginning from fw_from 

            Returns Person objects, with included Events and Names
            ordered by Person.sortname
        """
        def _read_person_list(o_filter, limit):
            """ Read Person data from given fw_from 
            """
            # Select a) filter by user b) show Isotammi common data (too)
            show_by_owner = o_filter.use_owner_filter()
            show_with_common = o_filter.use_common()
            #print("read_my_persons_list: by owner={}, with common={}".format(show_by_owner, show_with_common))
            user = o_filter.user
            try:
                """
                               show_by_owner    show_all
                            +-------------------------------
                with common |  me + common      common
                no common   |  me                -
                """
                with shareds.driver.session() as session:
                    if show_by_owner:

                        if show_with_common: #1 get all with owner name for all
                            print("_read_person_list: by owner with common")
                            result = session.run(Cypher_person.read_all_persons_with_events_starting_name,
                                                 user=user, start_name=fw_from, limit=limit)
                            # Returns person, names, events, user

                        else: #2 get my own (no owner name needed)
                            print("_read_person_list: by owner only")
                            result = session.run(Cypher_person.read_my_persons_with_events_starting_name,
                                                 user=user, start_name=fw_from, limit=limit)
                            # Returns person, names, events

                    else: #3 == #1 simulates common by reading all
                        print("_read_person_list: common only")
                        result = session.run(Cypher_person.read_all_persons_with_events_starting_name, #user=user, 
                                             start_name=fw_from, limit=limit)
                        # Returns person, names, events, user

                    return result
            except Exception as e:
                print('Error _read_person_list: {} {}'.format(e.__class__.__name__, e))            
                raise      

        def owner_not_me(record):
            # Returns owner of this record, if available and not me
            if 'user' in record.keys():
                u = record['user']
                if u == o_filter.user:
                    return '-'
                else:
                    return record['user']
            return None


        persons = []
        fw_from = o_filter.next_person[1]     # next_person names [bw_from, fw_from]

        ustr = "user " + o_filter.user if o_filter.user else "no user"
        print("read_my_persons_list: Get {} persons from {!r} for {} starting at {!r}".\
              format(limit, o_filter.owner_str(), ustr, fw_from))
        result = _read_person_list(o_filter, limit)

        for record in result:
            ''' <Record 
                    person=<Node id=163281 labels={'Person'} 
                      properties={'sortname': 'Ahonius##Knut Hjalmar',  
                        'sex': '1', 'confidence': '', 'change': 1540719036, 
                        'handle': '_e04abcd5677326e0e132c9c8ad8', 'id': 'I1543', 
                        'priv': 1,'datetype': 19, 'date2': 1910808, 'date1': 1910808}> 
                    names=[<Node id=163282 labels={'Name'} 
                      properties={'firstname': 'Knut Hjalmar', 'type': 'Birth Name', 
                        'suffix': '', 'surname': 'Ahonius', 'order': 0}>] 
                    events=[[
                        <Node id=169494 labels={'Event'} 
                            properties={'datetype': 0, 'change': 1540587380, 
                            'description': '', 'handle': '_e04abcd46811349c7b18f6321ed', 
                            'id': 'E5126', 'date2': 1910808, 'type': 'Birth', 'date1': 1910808}>,
                         None
                         ]]>
            '''
            node = record['person']
            # The same person is not created again
            p = Person_combo.from_node(node)

            # Is this the same person as previous?
            if len(persons) > 0 \
                and persons[-1].uniq_id == p.uniq_id \
                and 'user' in record.keys():
                # Yes, do not create a new person
                persons[-1].owners.append(owner_not_me(record))
            else:

#             if take_refnames and record['refnames']:
#                 refnlist = sorted(record['refnames'])
#                 p.refnames = ", ".join(refnlist)
                for nnode in record['names']:
                    pname = Name.from_node(nnode)
                    p.names.append(pname)
        
                # Create a list with the mentioned user name, if present
                p.owners = [owner_not_me(record),]
                                                                                                                                    
                # Events
        
                for enode, pname, role in record['events']:
                    if enode != None:
                        e = Event_combo.from_node(enode)
                        e.place = pname or ""
                        if role and role != "Primary":
                            e.role = role
                        p.events.append(e)
    
                persons.append(p)   
    
        return (persons)


    def get_citation_id(self):
        """ Luetaan henkilön viittauksen id. """

        query = """
            MATCH (person:Person)-[r:CITATION]->(c:Citation)
                WHERE ID(person)={}
                RETURN ID(c) AS citation_ref
            """.format(self.uniq_id)
        return  shareds.driver.session().run(query)


    def get_event_data_by_id(self):
        """ Luetaan henkilön tapahtumien id:t.

            Korvaava versio models.gen.event_combo.Event_combo.get_connected_events_w_links
        """

        root = int(self.uniq_id)
        query = """
MATCH (person:Person)-[r:EVENT]->(event:Event)
  WHERE ID(person)=$pid
RETURN r.role AS eventref_role, ID(event) AS event_ref"""
        return  shareds.driver.session().run(query, {"pid": root})


    def get_families_by_id(self):
        """ Luetaan niiden perheiden id:t, jossa lapsena. """

        pid = int(self.uniq_id)
        query = """
MATCH (person:Person) <-[r:PARENT]- (family:Family)
  WHERE ID(person)=$pid
RETURN ID(family) AS uniq_id"""
        return  shareds.driver.session().run(query, {"pid": pid})


    def get_hlinks_by_id(self):
        """ Luetaan henkilön linkit """

        event_result = self.get_event_data_by_id()
        for event_record in event_result:
            self.event_ref.append(event_record["event_ref"])
            self.eventref_role.append(event_record["eventref_role"])

        media_result = self.get_media_id()
        for media_record in media_result:
            self.media_ref.append(media_record["media_ref"])

        family_result = self.get_parentin_id()
        for family_record in family_result:
            self.families_as_parent.append(family_record["family_ref"])

        citation_result = self.get_citation_id()
        for citation_record in citation_result:
            self.citation_ref.append(citation_record["citation_ref"])

        return


    def get_media_id(self):
        """ Luetaan henkilöön liittyvien medioiden id:t. """

        query = """
            MATCH (person:Person)-[r:MEDIA]->(obj:Media)
                WHERE ID(person)={}
                RETURN ID(obj) AS media_ref
            """.format(self.uniq_id)
        return  shareds.driver.session().run(query)


    def get_parentin_id(self):
        """ Luetaan henkilön syntymäperheen id """

        query = """
            MATCH (person:Person)<-[r:CHILD]-(family:Family)
                WHERE ID(person)={}
                RETURN ID(family) AS family_ref
            """.format(self.uniq_id)
        return  shareds.driver.session().run(query)


    def get_person_and_name_data_by_id(self):
        """ Luetaan henkilö ja hänen kaikki nimensä.
        """
        pid = int(self.uniq_id)
        query = """
MATCH (person:Person)-[r:NAME]->(name:Name)
  WHERE ID(person)=$pid
RETURN person, name
  ORDER BY name.order"""
        person_result = shareds.driver.session().run(query, {"pid": pid})
        self.id = None

        for person_record in person_result:
            if self.id == None:
                node = person_record["person"]
                self.from_node(node)

            if len(person_record["name"]) > 0:
                pname = Name()
                pname.order = person_record["name"]['order']
                pname.type = person_record["name"]['type']
                pname.firstname = person_record["name"]['firstname']
#                 pname.refname = person_record["name"]['refname']
                pname.surname = person_record["name"]['surname']
                pname.suffix = person_record["name"]['suffix']
                self.names.append(pname)


    def get_person_w_names(self):
        """ Returns Person with Names and Notes included.

            Luetaan kaikki henkilön tiedot ja nimet, huomautukset
        """
        result = shareds.driver.session().run(Cypher_person.get_w_names_notes, 
                                              pid=int(self.uniq_id))

        for record in result:
            # <Record person=<Node id=72087 labels={'Person'} 
            #    properties={'handle': '_dd4a3c371f72257f442c1c42759', 'id': 'I1054', 
            #        'priv': 1, 'sex': '1', 'confidence': '2.0', 'change': 1523278690}> 
            #    notes=[] 
            #    names=[<Node id=72088 labels={'Name'} 
            #            properties={'alt': '', 'firstname': 'Anthon', 'type': 'Also Known As', 
            #                'suffix': 'jun.', 'surname': 'Naht'}>, 
            #        <Node id=72089 labels={'Name'} 
            #            properties={'alt': '1', 'firstname': 'Anthonius', 'type': 'Birth Name', 
            #                'suffix': '', 'surname': 'Naht'}>]
            # >
            node = record['person']
            self.from_node(node, obj=self)

            for node in record["names"]:
                pname = Name.from_node(node)
                self.names.append(pname)

            for note_id in record["notes"]:
                self.note_ref.append(note_id)


    @staticmethod
    def get_people_with_same_birthday():
        """ Etsi kaikki henkilöt, joiden syntymäaika on sama. 
        
            #TODO: p1.est_birth ei enää käytössä
        """

        query = """
            MATCH (p1:Person)-[r1:NAME]->(n1:Name) WHERE p1.est_birth<>''
            MATCH (p2:Person)-[r2:NAME]->(n2:Name) WHERE ID(p1)<ID(p2) AND
                p2.sex = p1.sex AND p2.est_birth = p1.est_birth
                RETURN COLLECT ([ID(p1), p1.est_birth, p1.est_death,
                n1.firstname, n1.suffix, n1.surname,
                ID(p2), p2.est_birth, p2.est_death,
                n2.firstname, n2.suffix, n2.surname]) AS ids
            """.format()
        return shareds.driver.session().run(query)


    @staticmethod
    def get_people_with_same_deathday():
        """ Etsi kaikki henkilöt, joiden kuolinaika on sama 
        
            #TODO: p1.est_death ei enää käytössä"""

        query = """
            MATCH (p1:Person)-[r1:NAME]->(n1:Name) WHERE p1.est_death<>''
            MATCH (p2:Person)-[r2:NAME]->(n2:Name) WHERE ID(p1)<ID(p2) AND
                p2.sex = p1.sex AND p2.est_death = p1.est_death
                RETURN COLLECT ([ID(p1), p1.est_birth, p1.est_death,
                n1.firstname, n1.suffix, n1.surname,
                ID(p2), p2.est_birth, p2.est_death,
                n2.firstname, n2.suffix, n2.surname]) AS ids
            """.format()
        return shareds.driver.session().run(query)


    @staticmethod
    def get_people_wo_birth():
        """ Etsitään henkilöt ilman syntymätapahtumaa.
        """

        query = """
 MATCH (p:Person) WHERE NOT EXISTS ((p)-[:EVENT]->(:Event {type:'Birth'}))
 WITH p
 MATCH (p)-[:NAME]->(n:Name)
 RETURN ID(p) AS uniq_id, p, n ORDER BY n.surname, n.firstname"""

        result = shareds.driver.session().run(query)

        titles = ['uniq_id', 'handle', 'change', 'id', 'priv', 'sex',
                  'firstname', 'surname']
        lists = []

        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["p"]['handle']:
                data_line.append(record["p"]['handle'])
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
            if record["p"]['sex']:
                data_line.append(record["p"]['sex'])
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
        """ Etsitään vanhimmat henkilöt.
        
            Mukana vain ne, joilla on syntymä- ja kuolintapahtuma
        """

        persons_get_oldest = """
 MATCH (p:Person)-[:EVENT]->(a:Event) 
     WHERE EXISTS ((p)-[:EVENT]->(b:Event {type:'Birth'}))
 WITH p, b 
 MATCH (p)-[:EVENT]->(b:Event) 
     WHERE EXISTS ((p)-[:EVENT]->(d:Event {type:'Death'}))
 WITH p, b, d
 MATCH (p)-[:NAME]->(n:Name)
 RETURN ID(p) AS uniq_id, p, n, 
     [b.datetype, b.date1, b.date2] AS birth, 
     [d.datetype, d.date1, d.date2] AS death 
 ORDER BY n.surname, n.firstname"""
                
        result = shareds.driver.session().run(persons_get_oldest)

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
            if record['birth'][0] != None:
                birth = DateRange(record['birth'])
                birth_str = birth.estimate()
                birth_data = birth_str.split("-")
                data_line.append(str(birth))
            else:
                data_line.append('-')
                birth_data = [None, None, None]
            if record['death'][0] != None:
                death = DateRange(record['death'])
                death_str = death.estimate()
                death_data = death_str.split("-")
                data_line.append(str(death))
#                 death_str = record['death']
#                 death_data = death_str.split("-")
#                 data_line.append(record['death'])
            else:
                data_line.append('-')
                death_data = [None, None, None]


            # Counting the age when the dates are as YYYY-mm-dd
            if birth_data[0] != None and death_data[0] != None:
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
    def get_person_events (nmax=0, pid=None, names=None):
        """ Luetaan henkilöitä tapahtumineen kannasta.
        
        Usage:
            get_persons()               kaikki
            get_persons(pid=123)        tietty henkilö oid:n mukaan poimittuna
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
        │{"sex":"0","handle":"         │{} │{"surname":"Andersen","alt":""│
        │handle_6","change":0,"id":"6"}│   │,"type":"","suffix":"","firstn│
        │                              │   │ame":"Alexander","refname":""}│
        ├──────────────────────────────┼───┼──────────────────────────────┤
        """

        #TODO nmax now not available
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

        query = """
MATCH (n:Person) -[:NAME]->( k:Name) {0}
    OPTIONAL MATCH (n) -[r:EVENT]-> (e)
RETURN n.id, k.firstname, k.surname,
       COLLECT([e.name, e.kind]) AS events
    ORDER BY k.surname, k.firstname {1}""".format(where, qmax)

        return shareds.driver.session().run(query)


    @staticmethod
    def get_person_combos (keys, currentuser, take_refnames=False, order=0):
        """ Read Persons with Names, Events, Refnames (reference names) and Places.
        
            Version 0.1
            Called from models.datareader.read_persons_with_events
            
            UUSI KORVAAMAAN get_events_k:n

             a) selected by unique id
                keys=['uniq_id', uid]    by person's uniq_id (for table_person_by_id.html)
             b) selected by name
                keys=['all']             all
                keys=['surname', name]   by start of surname
                keys=['firstname', name] by start of the first of first names
                keys=['patronyme', name] by start of patronyme name
                keys=['refname', name]   by exact refname
            If currentuser is defined, select only her Events

            #TODO: take_refnames should determine, if refnames are returned, too
            #TODO: filter by owner
        """
        if keys:
            rule=keys[0]
            key=keys[1].title() if len(keys) > 1 else None
            #print("Selected {} '{}'".format(rule, key))
        else:
            rule="all"
            key=""
# ╒════════════════════╤════════════════════╤════════════════════╤════════════════════╤═════════╕
# │"person"            │"name"              │"refnames"          │"events"            │"initial"│
# ╞════════════════════╪════════════════════╪════════════════════╪════════════════════╪═════════╡
# │{"handle":"_da692a09│{"alt":"","firstname│["Helena","Brita","K│[["Primary",{"datety│"K"      │
# │bac110d27fa326f0a7",│":"Brita Helena","ty│lick"]              │pe":0,"change":15009│         │
# │"id":"I0119","priv":│pe":"Birth Name","su│                    │07890,"description":│         │
# │"","sex":"2","con   │ffix":"","surname":"│                    │"","handle":"_da692d│         │
# │fidence":"2.5","chan│Klick"}             │                    │0fb975c8e8ae9c4986d2│         │
# │ge":1507492602}     │                    │                    │3","attr_type":"","i│         │
# │                    │                    │                    │d":"E0161","date2":1│         │
# │                    │                    │                    │754183,"type":"Birth│         │
# │                    │                    │                    │","date1":1754183,"a│         │
# │                    │                    │                    │ttr_value":""},null]│         │
# │                    │                    │                    │,...]               │         │
# └────────────────────┴────────────────────┴────────────────────┴────────────────────┴─────────┘

        try:
            with shareds.driver.session() as session:
                if rule == 'uniq_id':
                    return session.run(Cypher_person.get_events_uniq_id, id=int(key))
                elif rule == 'refname':
                    return session.run(Cypher_person.get_events_by_refname, name=key)
                elif rule == 'all':
                    if order == 1:      # order by first name
                        return session.run(Cypher_person.get_events_all_firstname)
                    elif order == 2:    # order by patroname
                        return session.run(Cypher_person.get_events_all_patronyme)
                    else:
                        return session.run(Cypher_person.get_events_all)
                else:
                    # Selected names and name types (untested?)
                    return session.run(Cypher_person.get_events_by_refname_use,
                                       attr={'use':rule, 'name':key})
        except Exception as err:
            print("iError get_person_combos: {1} {0}".format(err, keys), file=stderr)


    @staticmethod
    def get_events_k (keys, currentuser, take_refnames=False, order=0):
        """ OBSOLETE Read Persons with Names, Events and Refnames (reference names)

            - tilalle tulee Person_combo.get_person_combos
            Called from models.datareader.read_persons_with_events

             a) selected by unique id
                keys=['uniq_id', uid]    by person's uniq_id (for table_person_by_id.html)
             b) selected by name
                keys=['all']             all
                keys=['surname', name]   by start of surname
                keys=['firstname', name] by start of the first of first names
                keys=['patronyme', name] by start of patronyme name
                keys=['refname', name]   by exact refname
            If currentuser is defined, select only her Events

            #TODO: take_refnames should determine, if refnames are returned, too
        """
        if keys:
            rule=keys[0]
            key=keys[1].title() if len(keys) > 1 else None
            print("Selected {} '{}'".format(rule, key))
        else:
            rule="all"
            key=""

# ╒═════╤════════════════╤═══════════╤════════╤═════════════════╤═════════════════╕
# │"id" │"firstname"     │"surname"  │"suffix"│"refnames"       │"events"         │
# ╞═════╪════════════════╪═══════════╪════════╪═════════════════╪═════════════════╡
# │31844│"August Wilhelm"│"Wallenius"│""      │["August","Wilhel│[[29933,"Baptism"│
# │     │                │           │        │m","Wallenius"]  │, ...            │
# └─────┴────────────────┴───────────┴────────┴─────────────────┴─────────────────┘
# There is also fields confidence, est_birth, est_death, which are empty for now

#TODO: filter by owner

        try:
            with shareds.driver.session() as session:
                if rule == 'uniq_id':
                    return session.run(Cypher_person.get_events_uniq_id, id=int(key))
                elif rule == 'refname':
                    return session.run(Cypher_person.get_events_by_refname, name=key)
                elif rule == 'all':
                    if order == 1:      # order by first name
                        return session.run(Cypher_person.get_events_all_firstname)
                    elif order == 2:    # order by patroname
                        return session.run(Cypher_person.get_events_all_patronyme)
                    else:
                        return session.run(Cypher_person.get_events_all)
                else:
                    # Selected names and name types (untested?)
                    return session.run(Cypher_person.get_events_by_refname_use,
                                       attr={'use':rule, 'name':key})
        except Exception as err:
            print("iError get_events_k: {1} {0}".format(err, keys), file=stderr)


    # Not in use!
    def get_my_places(self, cleartext_list=False):
        ''' Stores all Places with their Place_names in self.places list.

            Finds names which are connected to any personal Events
        '''

        get_places_w_names = """
match (p:Person) -[r:EVENT]-> (e:Event) -[:PLACE]-> (pl:Place)
    where id(p)=$pid
with r, e, pl
    optional match (pl) -[:NAME]-> (pname:Place_name)
    return r.role as r_role, id(e) as e_id, 
        pl as place, collect(pname) as pnames"""
    
# ╒═════════╤══════╤════════════════════════════════╤════════════════════════════════╕
# │"r_role" │"e_id"│"place"                         │"pnames"                        │
# ╞═════════╪══════╪════════════════════════════════╪════════════════════════════════╡
# │"Primary"│72501 │{"coord":[60.5,27.2],"handle":"_│[{"name":"Hamina","lang":""}]   │
# │         │      │de189e6c36c3f1e676c22ed6559","id│                                │
# │         │      │":"P0004","type":"Town","pname":│                                │
# │         │      │"Hamina","change":1536051348}   │                                │
# ├─────────┼──────┼────────────────────────────────┼────────────────────────────────┤
# │"Primary"│72500 │{"handle":"_ddd39c4088f165882c16│[{"name":"Kaivopuisto","lang":""│
# │         │      │0493e88","id":"P0001","type":"Bo│},{"name":"Brunspark","lang":"sv│
# │         │      │rough","pname":"Kaivopuisto","ch│"}]                             │
# │         │      │ange":1536051387}               │                                │
# └─────────┴──────┴────────────────────────────────┴────────────────────────────────┘

        result = shareds.driver.session().run(get_places_w_names, pid=self.uniq_id)
        for record in result:
            ''' <Record r_role='Primary' e_id=72501 pl_id=72486 
                    place=<Node id=72486 labels={'Place'} 
                        properties={'handle': '_de189e6c36c3f1e676c22ed6559', 
                        'change': 1536051348, 'id': 'P0004', 'type': 'Town', 
                        'pname': 'Hamina', 'coord': [60.5, 27.2]}> 
                    pnames=[<Node id=72487 labels={'Place_name'} 
                        properties={'lang': '', 'name': 'Hamina'}>]>
            '''
            # Fill Place properties:
            #     handle
            #     change
            #     id                  esim. "P0001"
            #     type                str paikan tyyppi
            #     pname               str paikan nimi
            #     names[]:
            #        name             str paikan nimi
            #        lang             str kielikoodi
            #        dates            DateRange date expression

            e_id = record['e_id']
            
            for my_e in self.events:
                if e_id == my_e.uniq_id:
                    # Found current event, create a Place there
                    placerec = record['place']
                    print("event {}: {} <- place {}: {}".\
                          format(my_e.uniq_id, my_e, placerec.id, placerec['pname']))
                    # Get Place data
                    pl = Place()
                    pl.uniq_id = placerec.id
                    pl.type = placerec['type']
                    pl.pname = placerec['pname']
                    pl.id = placerec['id']
                    pl.handle = placerec['handle']
                    pl.change = placerec['change']
                    # Get the Place_names
                    for node in record['pnames']:
                        pn = Place_name.from_node(node)
                        pl.names.append(pn)

                    if cleartext_list:
                        my_e.clearnames = my_e.clearnames + pl.show_names_list()
                    my_e.place = pl

#         for e in self.events:
#             print("event {}: {}".format(e.uniq_id, e))
#             if e.place == None:
#                 print("- no place")
#             else:
#                 for n in e.place.names:
#                     print("- place {} name {}: {}".format(e.place.uniq_id, n.uniq_id, n))


#     def get_all_notes(self):
#         ''' Finds all Note and Weburl
#             which are connected to Person, Events or Families
#             and stores them in self.notes and self.Weburl lists
#         '''
#         #TODO Mihin tarvitaan?
#         pass


    @staticmethod
    def get_family_members (uniq_id):
        """ Read the Families and member names connected to given Person.

            for '/scene/person=<string:uniq_id>'
        """

        return shareds.driver.session().run(Cypher_family.get_persons_family_members, 
                                            pid=int(uniq_id))


    @staticmethod
    def get_refnames(pid):
        """ List Person's all Refnames with name use. """
        # ╒══════════════════════════╤═════════════════════╕
        # │"a"                       │"li"                 │
        # ╞══════════════════════════╪═════════════════════╡
        # │{"name":"Alfonsus","source│[{"use":"firstname"}]│
        # │":"Messu- ja kalenteri"}  │                     │
        # ├──────────────────────────┼─────────────────────┤
        # │{"name":"Bert-not-exists"}│[{"use":"firstname"}]│
        # └──────────────────────────┴─────────────────────┘
        query = """
MATCH (p:Person) WHERE ID(p) = $pid
MATCH path = (a) -[:BASENAME*]-> (p)
RETURN a, [x IN RELATIONSHIPS(path)] AS li
"""
        return shareds.driver.session().run(query, pid=pid)

 
    @staticmethod
    def get_ref_weburls(pid_list):
        """ Get all weburls referenced from list of uniq_ids.

            #TODO Mitä tietoja halutaan?
        """
        query="""
match (x) where id(x) in $pids
with distinct x
  match (x) -[r:CITATION|SOURCE|NOTE]-> (y) 
  return id(x) as root, x.id as root_id, type(r) as rtype, 
         id(y) as target, labels(y)[0] as label, y.id as id 
  order by root, id"""
 
        return shareds.driver.session().run(query, pids=pid_list)

# Unused methods:
#     def join_events(self, events, kind=None):
#         """
#         Päähenkilöön self yhdistetään tapahtumat listalta events.
#         Yhteyden tyyppi on kind, esim. "OSALLISTUI"
#         """
#         print("**** person.join_events() on toteuttamatta!")
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
#
#     def join_persons(self, others):
#         """
#         Päähenkilöön self yhdistetään henkilöiden others tiedot ja tapahtumat
#         """
#         #TODO Kahden henkilön ja heidän tapahtumiensa yhdistäminen
#         othersList = ""
#         for i in others:
#             othersList.append(str(i) + " ")
#         logging.debug("Yhdistetään henkilöön {} henkilöt {}".format(str(self), othersList))
#         pass
#

    def get_points_for_compared_data(self, comp_person, print_out=True):
        """ Tulostaa kahden henkilön tiedot vieretysten. """

        points = 0
        print ("*****Person*****")
        if (print_out):
            print ("Handle: " + self.handle + " # " + comp_person.handle)
            print ("Change: {} # {}".format(self.change, comp_person.change))
            print ("Unique id: " + str(self.uniq_id) + " # " + str(comp_person.uniq_id))
            print ("Id: " + self.id + " # " + comp_person.id)
            print ("Priv: " + self.priv + " # " + comp_person.priv)
            print ("Sex: " + self.sex + " # " + comp_person.sex)
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
                alt1.append(pname.order)
                type1.append(pname.type)
                first1.append(pname.firstname)
#                 refname1.append(pname.refname)
                surname1.append(pname.surname)
                suffix1.append(pname.suffix)

            names2 = comp_person.names
            for pname in names2:
                alt2.append(pname.order)
                type2.append(pname.type)
                first2.append(pname.firstname)
#                 refname2.append(pname.refname)
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
    def estimate_lifetimes(tx, uids=[]):
        """ Sets an estimated lifietime to Person.lifetime.

            Stores it as Person properties: datetype, date1, and date2

            The argument 'uids' is a list of uniq_ids of Person nodes; if empty,
            sets all lifetimes.

            Asettaa kaikille tai valituille henkilölle arvioidut syntymä- ja kuolinajat
            
            Called from bp.gramps.xml_dom_handler.DOM_handler.set_estimated_dates
            and models.dataupdater.set_estimated_dates
        """
        try:
            if not uids:
                result = tx.run(Cypher_person.set_est_lifetimes_all)
            else:
                if isinstance(uids, int):
                    uids = [uids]
                result = tx.run(Cypher_person.set_est_lifetimes, idlist=uids)
        except Exception as err:
            print("iError (Person_combo.save:estimate_lifetimes): {0}".format(err), file=stderr)
            return 0

        counters = result.consume().counters
        pers_count = int(counters.properties_set/3)
        print("Estimated lifetime for {} persons".format(pers_count))
        return pers_count


    def print_compared_data(self, comp_person, print_out=True):
        """ Tulostaa kahden henkilön tiedot vieretysten. """

        points = 0
        print ("*****Person*****")
        if (print_out):
            print ("Handle: " + self.handle + " # " + comp_person.handle)
            print ("Change: {} # {}".format(self.change, comp_person.change))
            print ("Id: " + self.id + " # " + comp_person.id)
            print ("Priv: " + self.priv + " # " + comp_person.priv)
            print ("Sex: " + self.sex + " # " + comp_person.sex)
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
                alt1.append(pname.order)
                type1.append(pname.type)
                first1.append(pname.firstname)
                surname1.append(pname.surname)
                suffix1.append(pname.suffix)

            names2 = comp_person.names
            for pname in names2:
                alt2.append(pname.order)
                type2.append(pname.type)
                first2.append(pname.firstname)
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
                        print ("Surname: " + surname1[i] + " # " + surname2[i])
                        print ("Suffix: " + suffix1[i] + " # " + suffix2[i])
        return points


    def save(self, username, tx):
        """ Saves the Person object and possibly the Names, Events ja Citations.

            On return, the self.uniq_id is set
        """
        raise NotImplementedError("Person_combo.save() ei toteutettu, ks. Person_gramps.save()")



class Person_as_member(Person):
    """ A person as a family member.

        Extra properties:
            role         str 'child', 'father' or 'mother' # "CHILD", "FATHER" or "MOTHER"
            birth_date   str '1749-11-02'
            names[]      Name
     """

    def __init__(self):
        """ Luo uuden instanssin """
        Person.__init__(self)
        self.role = ''
        self.birth_date = ''
        self.names = []

