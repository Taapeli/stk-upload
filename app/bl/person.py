'''
    Person and Name classes

    Person hierarkiasuunnitelma 10.9.2018/JMä

    class bl.Person(): 
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

Created on 6.10.2020

@author: jm
'''
from flask_babelex import _
from datetime import datetime

from bl.base import NodeObject, Status
from pe.db_reader import DBreader

from models.source_citation_reader import get_citations_js

# Privacy rule: how many years after death
PRIVACY_LIMIT = 0

# Sex code values
SEX_UNKOWN = 0 
SEX_MALE = 1
SEX_FEMALE = 2
SEX_NOT_APPLICABLE = 9


class Person(NodeObject):
    """ Person object

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
        self.sex = SEX_UNKOWN
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
        where we are, either Person or PersonBl)

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
        last_year_allowed = datetime.now().year - PRIVACY_LIMIT
        obj.too_new = obj.death_high > last_year_allowed
        return obj


class PersonReader(DBreader):
    '''
        Data reading class for Person objects with associated data.

        - Uses pe.db_reader.DBreader.__init__(self, dbdriver, u_context) 
          to define the database driver and user context

        - Returns a Result object.
    '''
    def get_person_search(self, args):
        """ Read Persons with Names, Events, Refnames (reference names) and Places
            and Researcher's username.
        
            Search by name by args['rule'], args['key']:
                rule=all                  all
                rule=surname, key=name    by start of surname
                rule=firstname, key=name  by start of the first of first names
                rule=patronyme, key=name  by start of patronyme name
                rule=refname, key=name    by exact refname
            Time limiting by args['years']:
                years='y1'    single year
                years='y1-'   from year
                years='y1-y2' year range
                years='-y2'   untill year
        """
        if 'years' in args:
            # Any of
            #     ['1800']
            #     ['1800', '']
            #     ['', '1800']
            #     ['1800', '1900']
            #     ['']
            lim = args['years'].split('-')
            if len(lim) < 2:
                lim.append(lim[0])
            y1 = int(lim[0]) if lim[0] > '' else -9999
            y2 = int(lim[1]) if lim[1] > '' else 9999
            if y1 > y2:
                (y1,y2) = (y2,y1)
            args['years'] = (y1, y2)
        else:
            args['years'] = (-9999, 9999)

        context = self.user_context
        args['use_user'] = self.use_user
        args['fw'] = context.next_name_fw()
        args['limit'] = context.count
        
        result = self.dbdriver.dr_get_person_list(args)
        # {'items': persons, 'status': Status.OK}

        if result.get('status') == Status.ERROR:
            msg = result.get("statustext")
            logger.error(f'bl.person.PersonReader.get_person_search: {msg}')
            print(f'bl.person.PersonReader.get_person_search: {msg}')
            return {'items':[], 'status':result['status'], 
                    'statustext': _('No persons found')}

        # Update the page scope according to items really found
        persons = result['items']
        if len(persons) > 0:
            context.update_session_scope('person_scope', 
                                          persons[0].sortname, persons[-1].sortname, 
                                          context.count, len(persons))

        if self.use_user is None:
            persons2 = [p for p in persons if not p.too_new]
            num_hidden = len(persons) - len(persons2)
        else:
            persons2 = persons
            num_hidden = 0
        return {'items': persons2, 'num_hidden': num_hidden, 'status': Status.OK}


    def get_person_list(self):
        ''' List person data including all data needed to Person page.
        
            Calls Neo4jDriver.dr_get_person_list(user, fw_from, limit)
        '''
        context = self.user_context
        res_dict = {}
        args = {'use_user': self.use_user,
                'fw': context.next_name_fw(),
                'limit':context.count}
        result = self.dbdriver.dr_get_person_list(args)
        # {'items': persons, 'status': Status.OK}
        if (result['status'] != Status.OK):
            return {'items':None, 'status':result['status'], 
                    'statustext': _('No persons found')}

        # Update the page scope according to items really found
        persons = result['items']
        if len(persons) > 0:
            context.update_session_scope('person_scope', 
                                          persons[0].sortname, persons[-1].sortname, 
                                          context.count, len(persons))

        if self.use_user is None:
            persons2 = [p for p in persons if not p.too_new]
            num_hidden = len(persons) - len(persons2)
        else:
            persons2 = persons
            num_hidden = 0
        res_dict['status'] = Status.OK

        res_dict['num_hidden'] = num_hidden
        res_dict['items'] = persons2
        return res_dict


    def get_a_person(self, uuid:str):
        ''' Read a person from common data or user's own Batch.

            a)  If you have selected to use common approved data, 
                you can read both your own and passed data.
            b)  If you have not selected common data,
                you can read only your own data.
            
            --> Origin from models.gen.person_combo.Person_combo.get_my_person
        '''
        result = self.dbdriver.dr_get_person_by_uuid(uuid)
        # {'item', 'root': {'root_type', 'usernode', 'id'}, 'status'}

        if (result['status'] != Status.OK):
            return {'item':None, 'status':result['status'], 
                    'statustext': _('The person is not accessible')}
        person = result.get('item')

#Todo: scheck privacy
#         if use_common and self.person.too_new: 
#             return None, None, None

        # The original researcher data in result['root']:
        # - root_type    which kind of owner link points to this object
        # - usernode     the (original) owner of this object
        # - bid          Batch id, if any
        root = result.get('root')
        root_type = root.get('root_type')
        #node = root['usernode']
        #nodeuser = node.get('user', "")
        #bid = node.get('id', "")
        if self.use_user is None:
            # Select person from public database
            if root_type != "PASSED":
                return {'item': None, 'status': Status.NOT_FOUND,
                        'statustext': 'The person is not accessible'}
        else:
            # Select the person only if owned by user
            if root_type != "OWNS":
                return {'item': None, 'status': Status.NOT_FOUND,
                        'statustext': 'The person is not accessible'}
#             if use_common or user == 'guest':
#                 # Select person from public database
#                 if root_type != "PASSED":
#                     raise LookupError("Person {uuid} not allowed.")
#             else:
#                 # Select the person only if owned by user
#                 if root_type != "OWNS":
#                     print('Person_combo.get_my_person: Should  we allow reading these approved persons, too?')

            person.root = root
            return {'item': person, 'status': Status.OK}


    def get_person_data(self, uuid:str, args:dict):
        '''
        Get a Person with all connected nodes for display in Person page as object tree.
            
            Note. The args are not yet used.
            
        * Origin from bp.scene.scene_reader.get_person_full_data(uuid, owner, use_common=True)
    
        For Person data page we must have all business objects, which has connection
        to current Person. This is done in the following steps:
    
        1. (p:Person) --> (x:Name|Event)
        2. (p:Person) <-- (f:Family)
           for f
           (f) --> (fp:Person) -[*1]-> (fpn:Name)
           (f) --> (fe:Event)
        3. for z in p, x, fe, z, s, r
           (y) --> (z:Citation|Note|Media)
        4. for pl in z:Place, ph
           (pl) --> (pn:Place_name)
           (pl) --> (ph:Place)
        5. for c in z:Citation
           (c) --> (s:Source) --> (r:Repository)
        
            p:Person
              +-- x:Name
              |     +-- z:Citation (2)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
        (1)   +-- x:Event
              |     +-- z:Place
              |     |     +-- pn:Place_name
              |     |     +-- z:Place (hierarkia)
              |     |     +-- z:Citation (2)
              |     |     +-- z:Note (3)
              |     |     +-- z:Media (4)
              |     +-- z:Citation (2)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
              +-- f:Family
              |     +-- fp:Person
              |     |     +-- fpn:Name
              |     +-- fe:Event (1)
              |     +-- z:Citation (2)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
        (2)   +-- z:Citation
              |     +-- s:Source
              |     |     +-- r:Repository
              |     |     |     +-- z:Citation (2)
              |     |     |     +-- z:Note (3)
              |     |     |     +-- z:Media (4)
              |     |     +-- z:Citation (2)
              |     |     +-- z:Note (3)
              |     |     +-- z:Media (4)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
        (3)    +-- z:Note
              |     +-- z:Citation (2)
              |     +-- z:Media (4)
        (4)   +-- z:Media
                    +-- z:Citation (2)
                    +-- z:Note (3)
          
        The objects are stored in PersonReader.person object p tree.
        - x and f: included objects (in p.names etc)
        - others: reference to "PersonReader.objs" dictionary (p.citation_ref[] etc)
    
        For ex. Sources may be referenced multiple times and we want to process them 
        once only.
        '''
        # Objects by uniq_id, referred from current person
        self.dbdriver.objs = {}

        # 1. Read Person p, if not denied
        result = self.dbdriver.dr_get_person_by_uuid(uuid, user=self.use_user)
        # result = {'item', 'root': {'root_type', 'usernode', 'id'}, 'status'}
        status = result.get('status')
        if  status != Status.OK:
            # Not found, not allowd (person.too_new) or error
            return result
        person = result.get('item')
        root = result.get('root')   # Batch or Audit data

        # 2. (p:Person) --> (x:Name|Event)
        #person.read_person_names_events()
        result = self.dbdriver.dr_get_person_names_events(person.uniq_id)
        # result {'names', 'events', 'cause_of_death', 'status'}
        if  status == Status.OK:
            person.names = result.get('names')
            person.events = result.get('events')
            person.cause_of_death = result.get('cause_of_death')
        else:
            print(f'get_person_data: No names or events for person {uuid}')
        # 3. (p:Person) <-- (f:Family)
        #    for f
        #      (f) --> (fp:Person) -[*1]-> (fpn:Name) # members
        #      (fp)--> (me:Event{type:Birth})
        #      (f) --> (fe:Event)
        #person.read_person_families()
        result = self.dbdriver.dr_get_person_families(person.uniq_id)
        # result {'families_as_child', 'families_as_parent', 'family_events', 'status'}
        if  status == Status.OK:
            person.families_as_child = result.get('families_as_child')
            person.families_as_parent = result.get('families_as_parent')
            person.events = person.events + result.get('family_events')
        else:
            print(f'get_person_data: No families for person {uuid}')

        if not self.user_context.privacy_ok(person):
            person.remove_privacy_limit_from_families()
    
        #    Sort all Person and family Events by date
        person.events.sort()

#TODO:
        # 4. for pl in z:Place, ph
        #      (pl) --> (pn:Place_name)
        #      (pl) --> (pi:Place)
        #      (pi) --> (pin:Place_name)
        self.dbdriver.dr_get_object_places(person)
     
        # 5. Read their connected nodes z: Citations, Notes, Medias
        #    for y in p, x, fe, z, s, r
        #        (y) --> (z:Citation|Note|Media)
        new_objs = [-1]
        self.dbdriver.citations = {}
        while len(new_objs) > 0:
            new_objs = self.dbdriver.dr_get_object_citation_note_media(person, new_objs)

        # Calculate the average confidence of the sources
        if len(self.dbdriver.citations) > 0:
            summa = 0
            for cita in self.dbdriver.citations.values():
                summa += int(cita.confidence)
                 
            aver = summa / len(self.dbdriver.citations)
            person.confidence = "%0.1f" % aver # string with one decimal
     
        # 6. Read Sources s and Repositories r for all Citations
        #    for c in z:Citation
        #        (c) --> (s:Source) --> (r:Repository)
        self.dbdriver.dr_get_object_sources_repositories()
    
        # Create Javascript code to create source/citation list
        jscode = get_citations_js(self.dbdriver.objs)
    
        # Return Person with included objects,  and javascript code to create
        # Citations, Sources and Repositories with their Notes
        return {'person': person,
                'objs': self.dbdriver.objs,
                'jscode': jscode,
                'root': root,
                'status': Status.OK}


class PersonBl(Person):

    def __init__(self):
        '''
        Constructor creates a new PersonBl intance.
        '''
        Person.__init__(self)
        self.user = None                # Researcher batch owner, if any
        self.names = []                 # models.gen.person_name.Name

        self.events = []                # bl.event.EventBl
        #self.event_ref = []             # Event uniq_ids # Gramps event handles (?)
        #self.eventref_role = []         # ... and roles
        #self.event_birth = None         # For birth ans death events
        #self.event_death = None

        #self.citation_ref = []          # models.gen.citation.Citation
        #self.note_ref = []              # uniq_id of models.gen.note.Note
        self.notes = []                 # 
        #self.media_ref = []             # uniq_ids of models.gen.media.Media
                                        # (previous self.objref_hlink[])

        # Other variables
        #self.role = ''                  # Role in Family
        #self.families_as_child = []     # - Propably one only
        #self.families_as_parent =[]
        #self.parentin_hlink = []

    @staticmethod
    def set_sortname(tx, uniq_id, namenode):
        """ Sets a sorting key "Klick#Jönsdotter#Brita Helena" 
            using given default Name node
        """
        raise(NotImplementedError, "TODO: bl.person.PersonBl.set_sortname")
#         key = namenode.key_surname()
#         return tx.run(Cypher_person.set_sortname, id=uniq_id, key=key)

    @staticmethod
    def get_confidence (uniq_id=None):
        """ Voidaan lukea henkilön tapahtumien luotettavuustiedot kannasta
        """
        raise(NotImplementedError, "TODO: bl.person.PersonBl.get_confidence")
#         if uniq_id:
#             return shareds.driver.session().run(Cypher_person.get_confidence,
#                                                 id=uniq_id)
#         else:
#             return shareds.driver.session().run(Cypher_person.get_confidences_all)


    def set_confidence (self, tx):
        """ Sets a quality rate to this Person
            Voidaan asettaa henkilön tietojen luotettavuusarvio kantaan
        """
        raise(NotImplementedError, "TODO: bl.person.PersonBl.set_confidence")
#         return tx.run(Cypher_person.set_confidence,
#                       id=self.uniq_id, confidence=self.confidence)

    def remove_privacy_limit_from_families(self):
        ''' Clear privacy limitations from self.person's families.
        
            Origin from models.person_reader
        '''
        for family in self.person.families_as_child:
            self.remove_privacy_limit_from_family(family)
        for family in self.person.families_as_parent:
            self.remove_privacy_limit_from_family(family)

