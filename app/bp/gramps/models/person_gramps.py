'''
Created on 18.10.2018


    Person for gramps xml load includes operations for accessing
    - Person and her Names
    - related Events and Places
    
    class bp.gramps.models.person_gramps.Person_gramps(Person): 
        - __init__()
        - save(self, tx, batch_id)      Tallettaa Person, Names, Events ja Citations


@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi> 
@author: Juha Mäkeläinen <jpek@iki.fi> 18.10.2018
'''

import datetime
from sys import stderr
import shareds
from shareds import logger

from pe.neo4j.write_driver import Neo4jWriteDriver
from pe.db_writer import DBwriter
from models.gen.person import Person
from models.cypher_gramps import Cypher_person_w_handle
from models.gen.note import Note


class Person_gramps(Person):
    """ Henkilö
    
        From Person.__init__(): 
            uniq_id, handle, id, priv, sex, confidence, change

        Other properties:
            names[]:
               order           int index of name variations; number 0 is default name
               #alt            str muun nimen nro
               type            str nimen tyyppi
               firstname       str etunimi
               #refname        str referenssinimi (entinen toteutus)
               surname         str sukunimi
               suffix          str patronyymi
            confidence         str tietojen luotettavuus
            est_birth          str arvioitu syntymäaika
            est_death          str arvioitu kuolinaika

        The handles of referred objects are in variables:
            eventref_hlink[]    str tapahtuman handle
            - eventref_role[]   str edellisen rooli
            media_refs[]        list of MediaRefResult objects (ent. objref_hlink)
            parentin_hlink[]    str vanhempien uniq_id
            noteref_hlink[]     str huomautuksen uniq_id
            citationref_hlink[] str viittauksen uniq_id    (ent.citationref_hlink)
     """

    def __init__(self):
        """ Creates an Person_gramps instance for Person data xml load.
        """
        Person.__init__(self)

        # For embadded or referenced child objects, displaying Person page
        # @see Plan bp.scene.data_reader.connect_object_as_leaf

        self.names = []                 # models.gen.person_name.Name
        # Gramps handles (and roles)
        self.eventref_hlink = []        # handles of Events
        self.eventref_role = []         # ... and roles
        self.media_refs = []         # handles of Media [(handle,crop)]
        self.parentin_hlink = []        # handle for parent family
        self.noteref_hlink = []         # 
        self.citationref_hlink = []     # models.gen.citation.Citation
        
        # Program objects
        self.events = []                # models.gen.event_combo.Event_combo
        self.notes = []                 # models.gen.note.Note, used for
                                        # generated objects which have no hlink

        # Other variables ???
        self.est_birth = ''
        self.est_death = ''


    def save(self, tx, **kwargs):   # batch_id):
        """ Saves the Person object and possibly the Names, Events ja Citations.

            On return, the self.uniq_id is set
            
            @todo: Remove those referenced person names, which are not among
                   new names (:Person) --> (:Name) 
        """
        if 'batch_id' in kwargs:
            batch_id = kwargs['batch_id']
        else:
            raise RuntimeError(f"Person_gramps.save needs batch_id for {self.id}")

        dbdriver = Neo4jWriteDriver(shareds.driver, tx)
        db = DBwriter(dbdriver)
        today = str(datetime.date.today())

        self.uuid = self.newUuid()
        # Save the Person node under UserProfile; all attributes are replaced
        p_attr = {}
        try:
            p_attr = {
                "uuid": self.uuid,
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "priv": self.priv,
                "sex": self.sex,
                "confidence":self.confidence,
                "sortname":self.sortname
            }
            if self.dates:
                p_attr.update(self.dates.for_db())

            result = tx.run(Cypher_person_w_handle.create_to_batch, 
                            batch_id=batch_id, p_attr=p_attr, date=today)
            ids = []
            for record in result:
                self.uniq_id = record[0]
                ids.append(self.uniq_id)
                if len(ids) > 1:
                    print("iError updated multiple Persons {} - {}, attr={}".format(self.id, ids, p_attr))
                # print("Person {} ".format(self.uniq_id))
            if self.uniq_id == None:
                print("iWarning got no uniq_id for Person {}".format(p_attr))

        except Exception as err:
            logger.error(f"Person_gramps.save: {err} in Person {self.id} {p_attr}")
            #print("iError: Person_gramps.save: {0} attr={1}".format(err, p_attr), file=stderr)

        # Save Name nodes under the Person node
        for name in self.names:
            name.save(tx, parent_id=self.uniq_id)

        # Save web urls as Note nodes connected under the Person
        if self.notes:
            Note.save_note_list(tx, self)

        ''' Connect to each Event loaded from Gramps '''
        try:
            for i in range(len(self.eventref_hlink)):
                tx.run(Cypher_person_w_handle.link_event, 
                       p_handle=self.handle, 
                       e_handle=self.eventref_hlink[i], 
                       role=self.eventref_role[i])
        except Exception as err:
            logger.error(f"Person_gramps.save: {err} in linking Event {self.handle} -> {self.eventref_hlink[i]}")
            #print("iError: Person_gramps.save events: {0} {1}".format(err, self.id), file=stderr)

        # Make relations to the Media nodes and it's Note and Citation references
        db.media_save_w_handles(self.uniq_id, self.media_refs)


        # The relations to the Family node will be created in Family.save(),
        # because the Family object is not yet created

        # Make relations to the Note nodes
        try:
            for handle in self.noteref_hlink:
                tx.run(Cypher_person_w_handle.link_note,
                       p_handle=self.handle, n_handle=handle)
        except Exception as err:
            logger.error(f"Person_gramps.save: {err} in linking Notes {self.handle} -> {handle}")

        # Make relations to the Citation nodes
        try:
            for handle in self.citationref_hlink:
                tx.run(Cypher_person_w_handle.link_citation,
                       p_handle=self.handle, c_handle=handle)
        except Exception as err:
            logger.error(f"Person_gramps.save: {err} in linking Citations {self.handle} -> {handle}")
        return

