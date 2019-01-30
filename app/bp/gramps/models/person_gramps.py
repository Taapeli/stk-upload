'''
Created on 18.10.2018


    Person for gramps xml load includes operations for accessing
    - Person and her Names
    - related Events and Places
    
    class bp.gramps.models.person_gramps.Person_gramps(Person): 
        - __init__()
        - save(self, username, tx)      Tallettaa Person, Names, Events ja Citations


@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi> 
@author: Juha Mäkeläinen <jpek@iki.fi> 18.10.2018
'''

import datetime
from sys import stderr
#import logging

import models.dbutil

from models.gen.person import Person
from models.cypher_gramps import Cypher_person_w_handle


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
            objref_hlink[]      str median handle
            parentin_hlink[]    str vanhempien uniq_id
            noteref_hlink[]     str huomautuksen uniq_id
            citationref_hlink[] str viittauksen uniq_id    (ent.citationref_hlink)
     """

    def __init__(self):
        """ Creates an Person_gramps instance for Person data xml load
        """
        Person.__init__(self)

        # For emadded or referenced child objects, displaying Person page
        # @see Plan bp.scene.data_reader.connect_object_as_leaf

        self.names = []                 # models.gen.person_name.Name
        # Gramps handles (and roles)
        self.eventref_hlink = []        # handles of Events
        self.eventref_role = []         # ... and roles
        self.objref_hlink = []          # handles of Media
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


    def save(self, tx, batch_id):
        """ Saves the Person object and possibly the Names, Events ja Citations

            On return, the self.uniq_id is set
            
            @todo: Remove those referenced person names, which are not among
                   new names (:Person) --> (:Name) 
        """

        today = str(datetime.date.today())
        if not self.handle:
            handles = models.dbutil.get_new_handles(3)
            self.handle = handles.pop()

        # Save the Person node under UserProfile; all attributes are replaced
        try:
            p_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "priv": self.priv,
                "sex": self.sex,
                "confidence":self.confidence,
                "sortname":self.sortname
            }
            if self.lifetime:
                p_attr.update(self.lifetime.for_db())

            result = tx.run(Cypher_person_w_handle.create_to_batch, 
                            batch_id=batch_id, p_attr=p_attr, date=today)
#             self.uniq_id = result.single()[0]
            for res in result:
                self.uniq_id = res[0]
                print("Person {} ".format(self.uniq_id))
            if self.uniq_id == None:
                print("Person <MISSING uniq_id> {}".format(p_attr))

        except Exception as err:
            print("Virhe (Person.save:Person): {0}".format(err), file=stderr)

        # Save Name nodes under the Person node
        for name in self.names:
            name.save(tx, self.uniq_id)

        # Save web urls as Note nodes connected under the Person
        for note in self.notes:
            note.save(tx, self.uniq_id)

        if len(self.events) > 0:
            # Make Event relations (if Events were stored in self.events)
            # TODO: onkohan tämä käytössä? Ei ainakaan gramps-latauksessa
            ''' Create and connect to an Person.event[*] '''
            for e in self.events:
                if handles:
                    e.handle = handles.pop()
                e_attr = {
                    "handle": e.handle,
                    "id": e.id,
                    "name": e.name, # "e_type": e.tyyppi,
                    "date": e.date,
                    "descr": e.description
                }
                try:
                    tx.run(Cypher_person_w_handle.link_event_embedded, 
                           p_handle=self.handle, e_attr=e_attr, role="osallistuja")
                except Exception as err:
                    print("Virhe (Person.save:create Event): {0}".format(err), file=stderr)

        # Make Event relations by hlinks (from gramps_loader)
        elif len(self.eventref_hlink) > 0:
            ''' Connect to each Event loaded from Gramps '''
            for i in range(len(self.eventref_hlink)):
                try:
                    tx.run(Cypher_person_w_handle.link_event, 
                           p_handle=self.handle, 
                           e_handle=self.eventref_hlink[i], 
                           role=self.eventref_role[i])
                except Exception as err:
                    print("Virhe (Person.save:Event): {0}".format(err), file=stderr)

        # Make relations to the Media nodes
        if len(self.objref_hlink) > 0:
            for ref in self.objref_hlink:
                try:
                    tx.run(Cypher_person_w_handle.link_media, 
                           p_handle=self.handle, m_handle=ref)
                except Exception as err:
                    print("Virhe (Person.save:Media): {0}".format(err), file=stderr)

        # The relations to the Family node will be created in Family.save(),
        # because the Family object is not yet created

        # Make relations to the Note nodes
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                try:
                    tx.run(Cypher_person_w_handle.link_note,
                           p_handle=self.handle, n_handle=self.noteref_hlink[i])
                except Exception as err:
                    print("Virhe (Person.save:Note): {0}".format(err), file=stderr)

        # Make relations to the Citation node
        if len(self.citationref_hlink) > 0: #TODO Many citations!
            try:
                tx.run(Cypher_person_w_handle.link_citation,
                       p_handle=self.handle, c_handle=self.citationref_hlink[0])
            except Exception as err:
                print("Virhe (Person.save:Citation): {0}".format(err), file=stderr)
        return

