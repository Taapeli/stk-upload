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
            uniq_id, handle, id, priv, gender, confidence, change

        Other properties:
            names[]:
               alt             str muun nimen nro
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

            urls[]              list of Weburl nodes
                priv           int 1 = salattu tieto
                href           str osoite
                type           str tyyppi
                description    str kuvaus
    
     """

    def __init__(self):
        """ Creates an Person_gramps instance for Person data xml load
        """
        Person.__init__(self)

        # For emadded or referenced child objects, displaying Person page
        # @see Plan bp.scene.models.connect_object_as_leaf

        self.names = []                 # models.gen.person_name.Name
        # Gramps handles (and roles)
        self.eventref_hlink = []        # handles of Events
        self.eventref_role = []         # ... and roles
        self.objref_hlink = []          # handles of Media
        self.parentin_hlink = []        # handle for parent family
        self.noteref_hlink = []         # 
        self.citationref_hlink = []          # models.gen.citation.Citation
        
        # Program objects
        self.urls = []
        self.events = []                # models.gen.event_combo.Event_combo

        # Other variables ???

        self.est_birth = ''
        self.est_death = ''


    def save(self, username, tx):
        """ Saves the Person object and possibly the Names, Events ja Citations

            On return, the self.uniq_id is set
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
                "gender": self.gender
            }
            result = tx.run(Cypher_person_w_handle.create, 
                            username=username, p_attr=p_attr, date=today)
#             self.uniq_id = result.single()[0]
            for res in result:
                self.uniq_id = res[0]
                print("Person {} ".format(self.uniq_id))

        except Exception as err:
            print("Virhe (Person.save:Person): {0}".format(err), file=stderr)

        # Save Name nodes under the Person node
        try:
            for name in self.names:
                n_attr = {
                    "alt": name.alt,
                    "type": name.type,
                    "firstname": name.firstname,
#                     "refname": name.refname,
                    "surname": name.surname,
                    "suffix": name.suffix
                }
                tx.run(Cypher_person_w_handle.link_name, 
                       n_attr=n_attr, p_handle=self.handle)
        except Exception as err:
            print("Virhe (Person.save:Name): {0}".format(err), file=stderr)

        # Save Weburl nodes under the Person
        for url in self.urls:
            u_attr = {
                "priv": url.priv,
                "href": url.href,
                "type": url.type,
                "description": url.description
            }
            try:
                tx.run(Cypher_person_w_handle.link_weburl, 
                       p_handle=self.handle, u_attr=u_attr)
            except Exception as err:
                print("Virhe (Person.save: {} create Weburl): {0}".\
                      format(self.id, err), file=stderr)

        if len(self.events) > 0:
            # Make Event relations (if Events were stored in self.events)
            # TODO: onkohan tämä käytössä?
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
            ''' Connect to each Event loaded form Gramps '''
            for i in range(len(self.eventref_hlink)):
                try:
                    tx.run(Cypher_person_w_handle.link_event, 
                           p_handle=self.handle, 
                           e_handle=self.eventref_hlink[i], 
                           role=self.eventref_role[i])
                except Exception as err:
                    print("Virhe (Person.save:Event): {0}".format(err), file=stderr)

        # Make relations to the Media node
        if len(self.objref_hlink) > 0:
            for ref in self.objref_hlink:
                try:
                    tx.run(Cypher_person_w_handle.link_media, 
                           p_handle=self.handle, m_handle=ref)
                except Exception as err:
                    print("Virhe (Person.save:Media): {0}".format(err), file=stderr)

        # The relations to the Family node will be created in Family.save(),
        # because the Family object is not yet created

        # Make relations to the Note node
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                try:
                    tx.run(Cypher_person_w_handle.link_note,
                           p_handle=self.handle, n_handle=self.noteref_hlink[i])
                except Exception as err:
                    print("Virhe (Person.save:Note): {0}".format(err), file=stderr)

        # Make relations to the Citation node
        if len(self.citationref_hlink) > 0:
            try:
                tx.run(Cypher_person_w_handle.link_citation,
                       p_handle=self.handle, c_handle=self.citationref_hlink[0])
            except Exception as err:
                print("Virhe (Person.save:Citation): {0}".format(err), file=stderr)
        return

