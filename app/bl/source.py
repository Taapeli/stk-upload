'''
    Source classes: Source, SourceBl and SourceReader.

    - Source       represents Source Node in database
    - SourceBl     represents Source and connected data (was Source_combo)
    - SourceReader has methods for reading Source and connected data
                   called from ui routes.py

Created on 3.5.2020
@author: jm

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py
@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>

'''
import logging 
logger = logging.getLogger('stkserver')
from flask_babelex import _

from .base import NodeObject, Status
from pe.db_reader import DBreader #, SourceResult

#Todo: move gen.Person_combo to bi.PersonBl
from models.gen.person_combo import Person_combo


class Source(NodeObject):
    """ Source
            
        Properties:
                handle          
                change
                id              esim. "S0001"
                stitle          str lähteen otsikko
        
        See also: bp.gramps.models.source_gramps.Source_gramps
     """

    def __init__(self, uniq_id=None):
        """ Luo uuden source-instanssin """
        NodeObject.__init__(self, uniq_id=uniq_id)
        self.stitle = ''
        self.sauthor = ''
        self.spubinfo = ''

    def __str__(self):
        return "{} '{}' '{}' '{}'".format(self.id, self.stitle, self.sauthor, self.spubinfo)

    @classmethod
    def from_node(cls, node):
        '''
        Transforms a db node to an object of type Source.
        '''
        # <Node id=355993 labels={'Source'}
        #     properties={'id': 'S0296', 'stitle': 'Hämeenlinnan lyseo 1873-1972',
        #         'uuid': 'c1367bbdc6e54297b0ef12d0dff6884f', 'spubinfo': 'Karisto 1973',
        #         'sauthor': 'toim. Mikko Uola', 'change': 1585409705}>

        s = cls()   # create a new Source, SourceBl
        s.uniq_id = node.id
        s.id = node['id']
        s.uuid = node['uuid']
        if 'handle' in node:
            s.handle = node['handle']
        s.stitle = node['stitle']
        s.sauthor = node['sauthor']
        s.spubinfo = node['spubinfo']
        s.sabbrev = node.get('sabbrev','')
        s.change = node['change']
        return s


class SourceBl(Source):
    """ Source with optional referenced data.
    
        Arrays repositories, citations, notes may contain business objects
        Array note_ref may contain database keys (uniq_ids)
    """

    def __init__(self, uniq_id=None):
        """ Creates a new PlaceBl instance.

            You may also give for printout eventuell hierarhy level
        """
        Source.__init__(self, uniq_id)

        # For display combo
        #Todo: onko repositories, citations käytössä?
        self.repositories = []
        self.citations = []
        self.notes = []
        self.note_ref = []



class SourceReader(DBreader):
    '''
        Data reading class for Source objects with associated data.

        - Use pe.db_reader.DBreader.__init__(self, dbdriver, u_context) 
          to define the database driver and user context

        - Returns a Result object which includes the tems and eventuel error object.
    '''

    def get_source_list(self):
        context = self.user_context
        fw = context.next_name_fw()
        kwargs = {"user": self.use_user, "fw": fw,  "count": context.count}
        if context.series:
            # Filtering by series (Lähdesarja)
            THEMES = {"birth": ('syntyneet','födda'),
                      "babtism": ('kastetut','döpta'),
                      "wedding": ('vihityt','vigda'),
                      "death": ('kuolleet','döda'),
                      "move": ('muuttaneet','flyttade')
                      }
            theme_fi, theme_sv = THEMES[context.series]
            kwargs["theme1"] = theme_fi 
            kwargs["theme2"] = theme_sv
        try:
            sources = self.dbdriver.dr_get_source_list_fw(**kwargs)
            results = {'sources':sources,'status':Status.OK}
    
            # Update the page scope according to items really found 
            if sources:
                context.update_session_scope('source_scope', 
                                              sources[0].stitle, sources[-1].stitle, 
                                              context.count, len(sources))
            else:
                return {'status':Status.NOT_FOUND}

            results = {'items':sources, 'status':Status.OK}
        except Exception as e:
            results = {'status':Status.ERROR, 'statustext':f"Source list: {e}"}
        return results


    def get_source_with_references(self, uuid, u_context):
        """ Read the source, repository and events etc referencing this source.
        
            Returns a dicitonary, where items = Source object.
            - item.notes[]      Notes connected to Source
            - item.repositories Repositories for Source
            - item.citations    Citating Persons, Events, Families and Medias
                                as [label, object] tuples(?)
        """
        source = self.dbdriver.dr_get_source_w_repository(self.use_user, uuid)
        results = {'item':source, 'status':Status.OK}
        if not source:
            results.error = f"DBreader.get_source_with_references: {self.use_user} - no Source with uuid={uuid}"
            return results
        
        citations, notes, targets = self.dbdriver.dr_get_source_citations(source.uniq_id)

        if len(targets) == 0:
            # Only Citations connected to Person Event or Family Event can be
            # processed. 
            #TODO: Should allow citating a Source from Place, Note, Meida etc

            results['status'] = Status.NOT_FOUND
            results['statustext'] = _('No person or family has uses this source')
            return results

        cit = []
        for c_id, c in citations.items():
            if c_id in notes:
                c.notes = notes[c_id]
            for target in targets[c_id]:
                if u_context.privacy_ok(target):
                    # Insert person name and life events
                    if isinstance(target, Person_combo):
                        self.dbdriver.dr_inlay_person_lifedata(target)
                    c.citators.append(target)
                else:
                    print(f'DBreader.get_source_with_references: hide {target}')

            cit.append(c)
        results['citations'] = cit

        return results
