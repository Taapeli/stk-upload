'''
Created on 3.5.2020

@author: jm
'''
import logging 
logger = logging.getLogger('stkserver')

from .base import NodeObject
from pe.db_reader import DBreader, SourceResult

# Obsolete
from models.gen.person_combo import Person_combo


class Source(NodeObject):
    """ Lähde
            
        Properties:
                handle          
                change
                id              esim. "S0001"
                stitle          str lähteen otsikko
        
        See also: bp.gramps.models.source_gramps.Source_gramps
     """

    def __init__(self):
        """ Luo uuden source-instanssin """
        NodeObject.__init__(self)
        self.stitle = ''
        self.sauthor = ''
        self.spubinfo = ''
        self.note_ref = []      # uniq_ids (previously note[])

        # For display combo
        #Todo: onko repositories, citations käytössä?
        self.repositories = []
        self.citations = []
        self.notes = []

    def __str__(self):
        return "{} '{}' '{}' '{}'".format(self.id, self.stitle, self.sauthor, self.spubinfo)


    @classmethod
    def from_node(cls, node):
        '''
        Transforms a db node to an object of type Source.
        
        <Node id=91394 labels={'Source'} 
            properties={'handle': '_d9edc4e4a9a6defc258', 'id': 'S0078', 
                'stitle': 'Kangasala syntyneet 1721-1778', 'change': '1507149115'}>
        '''
        s = cls()   # create a new Source
        s.uniq_id = node.id
        s.id = node['id']
        s.uuid = node['uuid']
        if 'handle' in node:
            s.handle = node['handle']
        s.stitle = node['stitle']
        s.sauthor = node['sauthor']
        s.spubinfo = node['spubinfo']
        s.change = node['change']
        return s


class SourceReader(DBreader):
    '''
        Data reading class for Source objects with associated data.

        - Use pe.db_reader.DBreader.__init__(self, dbdriver, u_context) 
          to define the database driver and user context

        - Returns a Result object which includes the tems and eventuel error object.
    '''

    def get_source_with_references(self, uuid, u_context):
        """ Read the source, repository and events etc referencing this source.
        
            Returns a SourceResult object, where items = SourceDb object.
            - item.notes[]      Notes connected to Source
            - item.repositories Repositories for Source
            - item.citations    Citating Persons, Events, Families and Medias
                                as [label, object] tuples(?)
                                
        """
        source = self.dbdriver.dr_get_source_w_repository(self.use_user, uuid)
        source_result = SourceResult(source)
        if not source:
            source_result.error = f"DBreader.get_source_with_references: {self.use_user} - no Source with uuid={uuid}"
            return source_result
        
        citations, notes, targets = self.dbdriver.dr_get_source_citations(source.uniq_id)

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

            source_result.citations.append(c)

        return source_result
