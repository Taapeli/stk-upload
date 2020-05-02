'''
    Person and Name classes

    Person hierarkiasuunnitelma 10.9.2018/JMä

    class gen.person.Person(): 
        Person-noden parametrit 
         - uniq_id
         - properties { handle:"_dd2c613026e7528c1a21f78da8a",
                        id:"I0000",
                        priv:None,
                        sex:"2",
                        confidence:"2.0",
                        sortname:"Floor#Hans-Johansdotter#Katarina",
                        datetype:20, date1:1863872, date2:1868992,
                        change:1536324580}

        - __init__()
        - __str__()
        - from_node(cls, node, obj=None) Creates/updates Person object from 
                                        neo4j Node object
        - get_confidence (uniq_id=None) Henkilön tapahtumien luotettavuustiedot
        - set_confidence (self, tx)     Asetetaan henkilön tietojen luotettavuusarvio
        
    class gen.person_combo.Person_combo(Person): 
        - __init__()
        - get_person_w_names(self)      Luetaan kaikki henkilön tiedot ja nimet
        - get_people_with_same_birthday() Etsi henkilöt, joiden syntymäaika on sama
        - get_people_with_same_deathday() Etsi henkilöt, joiden kuolinaika on sama
        - get_people_wo_birth()         Luetaan henkilöt ilman syntymätapahtumaa
        - get_old_people_top()          Henkilöt joilla syntymä- ja kuolintapahtuma
        - get_person_combos (keys, currentuser, take_refnames=False, order=0):
                                        Read Persons with Names, Events and Refnames
        - get_places(self)              Hakee liittyvät Paikat henkilöön
        - get_all_citation_source(self) Hakee liittyvät Cition ja Source
        - get_all_notes(self)           Hakee liittyvät Notet ja web linkit
        - get_family_members(uniq_id)   Luetaan liittyvät Names, Families and Events
        - get_refnames(pid)             Luetaan liittyvät Refnames

    class bp.gramps.models.person_gramps.Person_gramps(Person):
        - __init__()
        - save(self, tx)                Tallettaa Person, Names, Events ja Citations

    Not in use or obsolete:
    - from models.gen.person_combo.Person_combo(Person)
        - set_estimated_life()          Aseta est_birth ja est_death - Obsolete
    - from models.datareader.get_person_data_by_id 
      (returns list: person, events, photos, sources, families)
       #- get_hlinks_by_id(self)        Luetaan henkilön linkit (_hlink)
        - get_event_data_by_id(self)    Luetaan henkilön tapahtumien id:t
        - get_media_id(self)            Luetaan henkilön tallenteen id
    - from models.datareader.get_families_data_by_id and Person_combo.get_hlinks_by_id
       #- get_families_by_id(self)      Luetaan perheiden id:t
       #- get_parentin_id(self)         Luetaan henkilön syntymäperheen id
    - from Person_combo.get_hlinks_by_id
       #- get_citation_id(self)         Luetaan henkilöön liittyvän viittauksen id

    - table-näyttöjä varten
        - get_person_and_name_data_by_id(self)
                                        Luetaan kaikki henkilön tiedot ja nimet
        - get_points_for_compared_data(self, comp_person, print_out=True)
                                        Tulostaa kahden henkilön tiedot vieretysten
        - print_compared_data(self, comp_person, print_out=True) 
                                        Tulostaa kahden henkilön tiedot vieretysten


Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''
'''
    #Note:    The text field 'gender' is changed to another text field 'sex'
              following the standard recommendation, also in DB.


    The four codes specified in ISO/IEC 5218 are:
    
        0 = not known,
        1 = male,
        2 = female,
        9 = not applicable.
    
    The standard specifies that its use may be referred to by the designator "SEX". 
'''
from datetime import datetime

import shareds
from bl.base import NodeObject
from .cypher import Cypher_person
from .dates import DateRange

from flask_babelex import _

SEX_UNKOWN = 0 
SEX_MALE = 1
SEX_FEMALE = 2
SEX_NOT_APPLICABLE = 9


class Person(NodeObject):
    """ Henkilö

         - uniq_id                int database key
         - Node properties: {
            handle                str "_dd2c613026e7528c1a21f78da8a"
            id                    str "I0000"
            priv                  int 1 = merkitty yksityiseksi
            sex                   str "1", "2", "0" sukupuoli
            confidence            float "2.0" tietojen luotettavuus
            sortname              str default name as "surname#suffix#firstname"
            datetype,date1,date2  DateRange dates # estimated life time
            birth_low             int lifetime years estimate limits like 1720
            death_low             int
            birth_high            int
            death_high            int
            change                int 1536324580
           }
     """

    def __init__(self):
        """ Creates a new Person instance. """
        NodeObject.__init__(self)
        self.priv = None
        self.sex = 0
        self.confidence = ''
        self.sortname = ''
        self.dates = None    # Daterange: Estimated datetype, date1, date2

        self.birth_low = None
        self.death_low = None
        self.birth_high = None
        self.death_high = None

    def __str__(self):
        dates = self.dates if self.dates else ''
        return "{} {} {}".format(self.sex_str(), self.id, dates)

    def sex_str(self):
        " Returns person's sex as string"
        return self.convert_sex_to_str(self.sex)

    def sex_symbol(self):
        " Returns person's sex as string"
        symbols = {SEX_UNKOWN:'', 
                   SEX_MALE:'♂',
                   SEX_FEMALE:'♀',
                   SEX_NOT_APPLICABLE:'-'}
        return symbols.get(self.sex, '?')

    def child_by_sex(self):
        " Returns person's sex as string"
        ch = {SEX_UNKOWN:_('Child'), 
              SEX_MALE:_('Son'),
              SEX_FEMALE:_('Daughter'),
              SEX_NOT_APPLICABLE:_('Child')}
        return ch.get(self.sex, '?')

    @staticmethod
    def convert_sex_to_str(sex):
        " Returns sex code as string"

        sexstrings = {SEX_UNKOWN:_('sex not known'), 
                      SEX_MALE:_('male'),
                      SEX_FEMALE:_('female'),
                      SEX_NOT_APPLICABLE:_('sex not applicable')}
        return sexstrings.get(sex, '?')

    @staticmethod
    def sex_from_str(s):
        # Converts gender strings to ISO/IEC 5218 codes
        ss = s[:1].upper()
        if ss == 'M' or  ss == str(SEX_MALE):
            return SEX_MALE
        if ss == 'F' or ss == 'N' or ss == str(SEX_FEMALE):
            return SEX_FEMALE
        return 0
        
    @classmethod
    def from_node(cls, node, obj=None):
        '''
        Transforms a db node to an object of type Person.

        Youc can create a Person or Person_node instance. (cls is the class 
        where we are, either Person or Person_combo)

        <Node id=80307 labels={'Person'} 
            properties={'id': 'I0119', 'confidence': '2.5', 'sex': '2', 'change': 1507492602, 
            'handle': '_da692a09bac110d27fa326f0a7', 'priv': 1}>
        '''
        if not obj:
            obj = cls()
        obj.uuid = node.get('uuid')
        obj.uniq_id = node.id
        obj.id = node['id']
        obj.sex = node.get('sex', 'UNKNOWN')
        obj.change = node['change']
        obj.confidence = node.get('confidence', '')
        obj.sortname = node['sortname']
        obj.priv = node['priv']
        obj.birth_low = node['birth_low']
        obj.birth_high = node['birth_high']
        obj.death_low = node['death_low']
        obj.death_high = node['death_high']
        last_year_allowed = datetime.now().year - shareds.PRIVACY_LIMIT
        obj.too_new = obj.death_high > last_year_allowed
        if "datetype" in node:
            obj.dates = DateRange(node["datetype"], node["date1"], node["date2"])
        return obj


    @staticmethod
    def set_sortname(tx, uniq_id, namenode):
        """ Sets a sorting key "Klick#Jönsdotter#Brita Helena" 
            using given default Name node
        """
        key = namenode.key_surname()
        return tx.run(Cypher_person.set_sortname, id=uniq_id, key=key)
        
    @staticmethod
    def get_confidence (uniq_id=None):
        """ Voidaan lukea henkilön tapahtumien luotettavuustiedot kannasta
        """
        if uniq_id:
            return shareds.driver.session().run(Cypher_person.get_confidence,
                                                id=uniq_id)
        else:
            return shareds.driver.session().run(Cypher_person.get_confidences_all)


    def set_confidence (self, tx):
        """ Sets a quality rate to this Person
            Voidaan asettaa henkilön tietojen luotettavuusarvio kantaan
        """
        return tx.run(Cypher_person.set_confidence,
                      id=self.uniq_id, confidence=self.confidence)


    @staticmethod
    def get_total():
        """ Tulostaa henkilöiden määrän tietokannassa """

        query = "MATCH (p:Person) RETURN COUNT(p)"
        results =  shareds.driver.session().run(query)

        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Person*****")
        print ("Handle: " + self.handle)
        print ("Change: {}".format(self.change))
        print ("Id: " + self.id)
        print ("Priv: " + self.priv)
        print ("Sex: " + self.sex)
        print ("Sort name: " + self.sortname)

        if len(self.names) > 0:
            for pname in self.names:
                print ("Order: " + pname.order)
                print ("Type: " + pname.type)
                print ("First: " + pname.firstname)
#                 print ("Refname: " + pname.refname)
                print ("Surname: " + pname.surname)
                print ("Suffix: " + pname.suffix)

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
        for i in range(len(self.citation_ref)):
            print ("Citationref_hlink: " + self.citation_ref[i])
        return True
