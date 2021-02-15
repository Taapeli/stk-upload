#   Isotammi Geneological Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
#from sys import stderr
#import traceback
import logging 
logger = logging.getLogger('stkserver')
import shareds

from bl.base import NodeObject, Status
from bl.person_name import Name
from pe.db_reader import DbReader
from pe.db_writer import DbWriter
from pe.neo4j.cypher.cy_person import CypherPerson

from models.gen.note import Note
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
#         if obj.death_high < 9999:
#             print('ok? uniq_id=',obj.uniq_id,obj.death_high)
        obj.too_new = obj.death_high > last_year_allowed
        return obj


class PersonReader(DbReader):
    '''
        Data reading class for Person objects with associated data.

        - Uses pe.db_reader.DbReader.__init__(self, readservice, u_context) 
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
                rule=years, key=str       by possible living years:
                    str='-y2'   untill year
                    str='y1'    single year
                    str='y1-y2' year range
                    str='y1-'   from year
        """
        if args.get('rule') == 'years':
            try:
                lim = args['key'].split('-')
                y1 = int(lim[0]) if lim[0] > '' else -9999
                y2 = int(lim[-1]) if lim[-1] > '' else 9999
                if y1 > y2:
                    y2, y1 = [y1, y2]
                args['years'] = [y1, y2]
            except ValueError:
                return {'statustext':_('The year or years must be numeric'), 'status': Status.ERROR}

#         planned_search = {'rule':args.get('rule'), 'key':args.get('key'), 
#                           'years':args.get('years')}

        context = self.user_context
        args['use_user'] = self.use_user
        args['fw'] = context.first  # From here forward
        args['limit'] = context.count
        
        res = self.readservice.dr_get_person_list(args)
        # {'items': persons, 'status': Status.OK}

        status = res.get('status')
        if status == Status.ERROR:
            msg = res.get("statustext")
            logger.error(f'bl.person.PersonReader.get_person_search: {msg}')
            print(f'bl.person.PersonReader.get_person_search: {msg}')
            return {'items':[], 'status':status,
                    'statustext': _('No persons found')}

        # Update the page scope according to items really found
        persons = res['items']
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
        return {'items': persons2, 'num_hidden': num_hidden, 'status': status}


    def get_person_list(self):
        ''' List person data including all data needed to Person page.
        
            Calls Neo4jDriver.dr_get_person_list(user, fw_from, limit)
        '''
        context = self.user_context
        res_dict = {}
        args = {'use_user': self.use_user,
                'fw': context.first,  # From here forward
               'limit':context.count}
        res = self.readservice.dr_get_person_list(args)
        # {'items': persons, 'status': Status.OK}
        if Status.has_failed(res):
            return {'items':None, 'status':res['status'], 
                    'statustext': _('No persons found')}

        # Update the page scope according to items really found
        persons = res['items']
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
        res = self.readservice.dr_get_person_by_uuid(uuid)
        # {'item', 'root': {'root_type', 'usernode', 'id'}, 'status'}

        if Status.has_failed(res):
            return {'item':None, 'status':res['status'], 
                    'statustext': _('The person is not accessible')}
        person = res.get('item')

#Todo: scheck privacy
#         if use_common and self.person.too_new: 
#             return None, None, None

        # The original researcher data in res['root']:
        # - root_type    which kind of owner link points to this object
        # - usernode     the (original) owner of this object
        # - bid          Batch id, if any
        root = res.get('root')
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
        self.readservice.objs = {}

        # 1. Read Person p, if not denied
        res = self.readservice.dr_get_person_by_uuid(uuid, user=self.use_user)
        # res = {'item', 'root': {'root_type', 'usernode', 'id'}, 'status'}
        if Status.has_failed(res):
            # Not found, not allowd (person.too_new) or error
            if res.get('status') == Status.NOT_FOUND:
                return {'status':Status.NOT_FOUND, 
                        'statustext': _('Requested person not found')}
            return res
        person = res.get('item')
        root = res.get('root')   # Info about linked Batch or Audit node

        # 2. (p:Person) --> (x:Name|Event)
        res = self.readservice.dr_get_person_names_events(person.uniq_id)
        # result {'names', 'events', 'cause_of_death', 'status'}
        if  Status.has_failed(res):
            print(f'get_person_data: No names or events for person {uuid}')
        else:
            person.names = res.get('names')
            person.events = res.get('events')
            person.cause_of_death = res.get('cause_of_death')
        # 3. (p:Person) <-- (f:Family)
        #    for f
        #      (f) --> (fp:Person) -[*1]-> (fpn:Name) # members
        #      (fp)--> (me:Event{type:Birth})
        #      (f) --> (fe:Event)
        res = self.readservice.dr_get_person_families(person.uniq_id)
        # res {'families_as_child', 'families_as_parent', 'family_events', 'status'}
        if  Status.has_failed(res):
            print(f'get_person_data: No families for person {uuid}')
        else:
            person.families_as_child = res.get('families_as_child')
            person.families_as_parent = res.get('families_as_parent')
            person.events = person.events + res.get('family_events')

        if not self.user_context.use_common():
            person.remove_privacy_limit_from_families()

        #    Sort all Person and family Events by date
        person.events.sort()


        # 4. for pl in z:Place, ph
        #      (pl) --> (pn:Place_name)
        #      (pl) --> (pi:Place)
        #      (pi) --> (pin:Place_name)
        ret = self.readservice.dr_get_object_places(person)
        if  Status.has_failed(res):
            print(f'get_person_data: Event places read error: {ret.get("statustext")}')
     
        # 5. Read their connected nodes z: Citations, Notes, Medias
        #    for y in p, x, fe, z, s, r
        #        (y) --> (z:Citation|Note|Media)
        new_objs = [-1]
        self.readservice.citations = {}
        while len(new_objs) > 0:
            new_objs = self.readservice.dr_get_object_citation_note_media(person, new_objs)

        # Calculate the average confidence of the sources
        if len(self.readservice.citations) > 0:
            summa = 0
            for cita in self.readservice.citations.values():
                summa += int(cita.confidence)
                 
            aver = summa / len(self.readservice.citations)
            person.confidence = "%0.1f" % aver # string with one decimal
     
        # 6. Read Sources s and Repositories r for all Citations
        #    for c in z:Citation
        #        (c) --> (s:Source) --> (r:Repository)
        self.readservice.dr_get_object_sources_repositories()
    
        # Create Javascript code to create source/citation list
        jscode = get_citations_js(self.readservice.objs)
    
        # Return Person with included objects,  and javascript code to create
        # Citations, Sources and Repositories with their Notes
        return {'person': person,
                'objs': self.readservice.objs,
                'jscode': jscode,
                'root': root,
                'status': Status.OK}

    def get_surname_list(self, count=40):
        ''' 
        List all surnames so that they can be displayed in a name cloud.
        '''
        if self.use_user:
            surnames = self.readservice.dr_get_surname_list_by_user(self.use_user,
                                                                    count=count)
        else:
            surnames = self.readservice.dr_get_surname_list_common(count=count)
        # [{'surname': surname, 'count': count},...]
        return surnames

class PersonWriter(DbWriter):
    def __init__(self, writeservice, u_context):
        self.writeservice = writeservice
        self.u_context = u_context
    def set_primary_name(self, uuid, old_order):
        self.writeservice.dr_set_primary_name(uuid, old_order)
    def set_name_orders(self, uid_list):
        self.writeservice.dr_set_name_orders(uid_list)


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


    def save(self, tx, **kwargs):   # batch_id):
        """ Saves the Person object and possibly the Names, Events ja Citations.

            On return, the self.uniq_id is set
            
            @todo: Remove those referenced person names, which are not among
                   new names (:Person) --> (:Name) 
        """
        from bl.media import MediaWriter

        if 'batch_id' in kwargs:
            batch_id = kwargs['batch_id']
        else:
            raise RuntimeError(f"Person_gramps.save needs batch_id for {self.id}")
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

            result = tx.run(CypherPerson.create_to_batch, 
                            batch_id=batch_id, p_attr=p_attr) #, date=today)
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
            #for i in range(len(self.eventref_hlink)):
            for handle_role in self.event_handle_roles:
                # a tuple (event_handle, role)
                tx.run(CypherPerson.link_event, 
                       p_handle=self.handle, 
                       e_handle=handle_role[0], 
                       role=handle_role[1])
        except Exception as err:
            logger.error(f"Person_gramps.save: {err} in linking Event {self.handle} -> {self.handle_role}")
            #print("iError: Person_gramps.save events: {0} {1}".format(err, self.id), file=stderr)

        # Make relations to the Media nodes and it's Note and Citation references
        if self.media_refs:
            writer = MediaWriter(shareds.datastore.dataservice)
            writer.create_and_link_by_handles(self.uniq_id, self.media_refs)


        # The relations to the Family node will be created in Family.save(),
        # because the Family object is not yet created

        # Make relations to the Note nodes
        try:
            for handle in self.note_handles:
                tx.run(CypherPerson.link_note,
                       p_handle=self.handle, n_handle=handle)
        except Exception as err:
            logger.error(f"Person_gramps.save: {err} in linking Notes {self.handle} -> {handle}")

        # Make relations to the Citation nodes
        try:
            for handle in self.citation_handles:
                tx.run(CypherPerson.link_citation,
                       p_handle=self.handle, c_handle=handle)
        except Exception as err:
            logger.error(f"Person_gramps.save: {err} in linking Citations {self.handle} -> {handle}")
        return


    @staticmethod
    def update_person_confidences(person_ids:list):
        """ Sets a quality rate for given list of Person.uniq_ids.

            Person.confidence is calculated as a mean of confidences in
            all Citations used for Person's Events.
        """
        counter = 0
        ds = shareds.datastore.dataservice
        for uniq_id in person_ids:
            res = ds._update_person_confidences(uniq_id)
            # returns {confidence, status, statustext}
            stat = res.get('status')
            if stat == Status.UPDATED:
                counter += 1
            elif stat != Status.OK:
                # Update failed
                return {'status': stat, 'statustext':res.get('statustext')}

        return {'status':Status.OK, 'count':counter}

    @staticmethod
    def set_person_name_properties(uniq_id=None, ops=['refname', 'sortname']):
        """ Set Refnames to all Persons or one Person with given uniq_id; 
            also sets Person.sortname using the default name
    
            Called from bp.gramps.xml_dom_handler.DOM_handler.set_family_calculated_attributes,
                        bp.admin.routes.set_all_person_refnames
        """
        sortname_count = 0
        refname_count = 0
        do_refnames = 'refname' in ops
        do_sortname = 'sortname' in ops
        names = []
        ds = shareds.datastore.dataservice

        # Get each Name object (with person_uid) 
        for pid, name_node in ds.ds_get_personnames(uniq_id):
            name = Name.from_node(name_node)
            name.person_uid =  pid
            names.append(name)

        if do_refnames:
            for name in names:
                # Create links and nodes from given person: (:Person) --> (r:Refname)
                res = ds.ds_build_refnames(name.person_uid, name)
                if Status.has_failed(res): return res
                refname_count += res.get('count', 0)
        if do_sortname:
            for name in names:
                if name.order == 0:
                    # If default name, store sortname key to Person node
                    sortname = name.key_surname()
                    ds._set_person_sortname(name.person_uid, sortname)
                    if Status.has_failed(res): return res
                    sortname_count += 1
                    break

        return {'refnames': refname_count, 'sortnames': sortname_count, 
                'status':Status.OK}


#     @staticmethod
#     def get_confidence (uniq_id=None): --> pe.neo4j.dataservice.Neo4jWriteDriver.dr_get_person_confidences
#         """ Collect Person confidence from Person and the Event nodes.
# 
#             Voidaan lukea henkilön tapahtumien luotettavuustiedot kannasta
#         """
#         raise(NotImplementedError, "TODO: bl.person.PersonBl.get_confidence")
# 
#         if uniq_id:
#             return shareds.driver.session().run(Cypher_person.get_confidence,
#                                                 id=uniq_id)
# #         else:
# #             return shareds.driver.session().run(Cypher_person.get_confidences_all)

#     def set_confidence (self, tx): 
#         """ Sets a quality rate to this Person
#             Voidaan asettaa henkilön tietojen luotettavuusarvio kantaan
#         """
#         raise(NotImplementedError, "TODO: bl.person.PersonBl.set_confidence")
# #         return tx.run(Cypher_person.set_confidence,
# #                       id=self.uniq_id, confidence=self.confidence)

    @staticmethod
    def estimate_lifetimes(uids=[]): # <-- 
        """ Sets estimated lifetimes to Person.dates for given person.uniq_ids.
 
            Stores dates as Person properties: datetype, date1, and date2
 
            :param: uids  list of uniq_ids of Person nodes; empty = all lifetimes
 
            Called from bp.gramps.xml_dom_handler.DOM_handler.set_estimated_dates
            and models.dataupdater.set_estimated_dates
        """
        ds = shareds.datastore.dataservice
        res = ds._set_people_lifetime_estimates(uids)

        print(f"Estimated lifetime for {res['count']} persons")
        return res


    def remove_privacy_limit_from_families(self):
        ''' Clear privacy limitations from self.person's families.
        
            Origin from models.person_reader
        '''
        for family in self.families_as_child:
            family.remove_privacy_limits()
        for family in self.families_as_parent:
            family.remove_privacy_limits()

