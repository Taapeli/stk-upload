'''
    Citation class for handling Citation nodes and relations and
    NodeRef class to store data of referring nodes and Source

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from sys import stderr

import shareds
from .cypher import Cypher_citation
from models.cypher_gramps import Cypher_citation_w_handle


class Citation:
    """ Lähdeviittaus
            
        Properties:
                handle           str
                change           int
                id               esim. "C0001"
                dateval          str date
                page             str page description
                confidence       str confidence 0.0 - 5.0 (?)
                note_ref         int huomautuksen osoite (ent. noteref_hlink str)
                source_handle    str handle of source   _or_
                source_id        int uniq_id of a Source object
                citators         NodeRef nodes referring this citation
     """

    def __init__(self):
        """ Luo uuden citation-instanssin """
        self.uniq_id = None
        self.handle = ''
        self.change = 0
        self.id = ''
        self.dateval = ''
        self.page = ''
        self.confidence = ''
        self.mark = ''          # citation mark like '1a', if defined
        self.noteref_hlink = []
        self.source_handle = ''
        self.source_id = None   # uniq_ids of Source objects, for creating display sets
        self.citators = []      # Lähde-sivulle
        self.note_ref = []


    def __str__(self):
        return "{} '{}'".format(self.id, self.page)


    @classmethod
    def from_node(cls, node):
        '''
        Transforms a db node to an object of type Citation.
        '''
        n = cls()
        n.uniq_id = node.id
        n.handle = node['handle']
        n.change = node['change']
        n.id = node['id'] or ''
        n.confidence = node['confidence'] or ''
        n.dateval = node['dateva'] or None
        n.page = node['page'] or ''
        return n

    @staticmethod       
    def get_persons_citations (uniq_id):
        """ Read 'Person -> Event -> Citation' and 'Person -> Citation' paths

            Haetaan henkilön Citationit, suoraan tai välisolmujen kautta
            ja talleta niihin viittaaja (citator Event tai Person)
            
            Returns list of Citations and list of Source ids
        """
# ╒══════════════════════════════════════════════════════════════════════╤═══════════╕
# │"end"                                                                 │"source_id"│
# ╞══════════════════════════════════════════════════════════════════════╪═══════════╡
# │[{"datetype":0,"change":1521882842,"description":"","handle":"_dd7681e│91637      │
# │08a259cca1aa0c055cb2","attr_type":"","id":"E2820","date2":1869085,"typ│           │
# │e":"Birth","date1":1869085,"attr_value":""},                          │           │
# │                                            {"handle":"_dd768dca3a6265│           │
# │4475a5726dfcd","page":"s. 336 1825 Augusti 29 kaste 27","id":"C1362","│           │
# │dateval":"","confidence":"2","change":1521882911},{"handle":"_dd162a3b│           │
# │cb7533c6d1779e039c6","id":"S0409","stitle":"Askainen syntyneet 1783-18│           │
# │25","change":"1519858899"}]                                           │           │
# ├──────────────────────────────────────────────────────────────────────┼───────────┤
# │[{"handle":"_dd7686926d946cd18c5642e61e2","id":"C1361","page":"1891 Sy│91657      │
# │yskuu 22","dateval":"","change":1521882215,"confidence":"2"},{"handle"│           │
# │:"_dd3d7f7206c3ca3408c9daf6c58","id":"S0333","stitle":"Askainen kuolle│           │
# │et 1890-1921","change":"1520351255"}]                                 │           │
# ├──────────────────────────────────────────────────────────────────────┼───────────┤
# │[{"datetype":0,"change":1521882240,"description":"","handle":"_dd76825│91657      │
# │122e5977bf3ee88e213f","attr_type":"","id":"E2821","date2":1936694,"typ│           │
# │e":"Death","date1":1936694,"attr_value":""},                          │           │
# │                                            {"handle":"_dd7686926d946c│           │
# │d18c5642e61e2","id":"C1361","page":"1891 Syyskuu 22","dateval":"","cha│           │
# │nge":1521882215,"confidence":"2"},{"handle":"_dd3d7f7206c3ca3408c9daf6│           │
# │c58","id":"S0333","stitle":"Askainen kuolleet 1890-1921","change":"152│           │
# │0351255"}]                                                            │           │
# └──────────────────────────────────────────────────────────────────────┴───────────┘
        
        result = shareds.driver.session().run(Cypher_citation.get_persons_citation_paths, 
                                              pid=uniq_id)
        # Esimerkki:
        # ╒══════╤═════════════════════════════════════════════════╤═══════════╕
        # │"id_p"│"end"                                            │"source_id"│
        # ╞══════╪═════════════════════════════════════════════════╪═══════════╡
        # │80307 │[[88523,"E0076"],[90106,"C0046"],[91394,"S0078"]]│91394      │
        # ├──────┼─────────────────────────────────────────────────┼───────────┤
        # │80307 │[[90209,"C0038"],[91454,"S0003"]]                │91454      │
        # ├──────┼─────────────────────────────────────────────────┼───────────┤
        # │80307 │[[88533,"E0166"],[90343,"C0462"],[91528,"S0257"]]│91528      │
        # └──────┴─────────────────────────────────────────────────┴───────────┘
        # -liitä Event "E0076" -> "C0046", "C0046" -> "S0078"
        # -liitä Person  80307 -> "C0038", "C0038" -> "S0003"
        # -liitä Event "E0166" -> "C0462", "C0462" ->"S0257"
        citations = []
        source_ids = []
        for record in result:
            nodes = record['end']
            c = Citation()
            c.source_id = record['source_id']
            if len(source_ids) == 0 or c.source_id != source_ids[-1]:
                # Get data of this source
                source_ids.append(c.source_id)

            if len(nodes) == 1:
                # Direct link (:Person) --> (:Citation)
                # Nodes[0] ~ Citation
                # <Node id=89360 labels={'Citation'} 
                #       properties={'change': 1521882911, 
                #                   'handle': '_dd768dca3a62654475a5726dfcd', 
                #                   'page': 's. 336 1825 Augusti 29 kaste 27', 
                #                   'id': 'C1362', 'confidence': '2', 'dateval': ''
                #                  }>
                cit = nodes[0]
            else:
                # Longer path (:Person) -> (x) -> (:Citation)
                # Nodes[0] ~ Event (or something else)
                # Nodes[1] ~ Citation
                eve = nodes[0]
                cit = nodes[1]
                e = NodeRef()
                e.uniq_id = eve.id
                e.eventtype = eve['type']
                c.citators.append(e)

            c.uniq_id = cit.id
            c.id = cit['id']
            c.label = cit.labels.pop()
            c.page = cit['page']
            c.confidence = cit['confidence']

            citations.append(c)
        
        return [citations, source_ids]


    @staticmethod       
    def get_source_repo (uniq_id=None):
        """ Read Citation -> Source -> Repository chain
            and optionally Notes.            
            Citation has all data but c.handle

            Voidaan lukea annetun Citationin lähde ja arkisto kannasta
        """
        with shareds.driver.session() as session:
            if uniq_id:
                return session.run(Cypher_citation.get_cita_sour_repo, 
                                   uid=uniq_id)
            else:
                return session.run(Cypher_citation.get_cita_sour_repo_all)
            
        
    
    def get_sourceref_hlink(self):
        """ Voidaan lukea lähdeviittauksen lähteen uniq_id kannasta
        """
        
        query = """
 MATCH (citation:Citation)-[r:SOURCE]->(source:Source) WHERE ID(citation)={}
 RETURN ID(source) AS id
 """.format(self.uniq_id)
                
        result = shareds.driver.session().run(query)
        for record in result:
            if record['id']:
                self.source_handle = record['id']

    
    @staticmethod       
    def get_total():
        """ Tulostaa lähteiden määrän tietokannassa """
                        
        query = """
            MATCH (c:Citation) RETURN COUNT(c)
            """
        results = shareds.driver.session().run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Citation*****")
        print ("Handle: " + self.handle)
        print ("Change: {}".format(self.change))
        print ("Id: " + self.id)
        print ("Dateval: " + self.dateval)
        print ("Page: " + self.page)
        print ("Confidence: " + self.confidence)
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                print ("Noteref_hlink: " + self.noteref_hlink[i])
        if self.source_handle != '':
            print ("Sourceref_hlink: " + self.source_handle)
        return True


    def save(self, tx):
        """ Saves this Citation and connects it to it's Notes and Sources"""

        try:
            # Create a new Citation node
                
            c_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "dateval": self.dateval, 
                "page": self.page, 
                "confidence": self.confidence
            }
            tx.run(Cypher_citation_w_handle.create, c_attr=c_attr)
        except Exception as err:
            print("Virhe (Citation.save): {0}".format(err), file=stderr)
            raise SystemExit("Stopped due to errors")    # Stop processing
            #TODO raise ConnectionError("Citation.save: {0}".format(err))

        # Make relations to the Note nodes
        for hlink in self.noteref_hlink:
            try:
                tx.run(Cypher_citation_w_handle.link_note, 
                       handle=self.handle, hlink=hlink)
            except Exception as err:
                print("Virhe (Citation.save:Note hlink): {0}".format(err), file=stderr)

        try:   
            # Make relation to the Source node
            if self.source_handle != '':
                tx.run(Cypher_citation_w_handle.link_source,
                       handle=self.handle, hlink=self.source_handle)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
        return


class NodeRef():
    ''' Carries data of citating nodes
            label            str (optional) Person or Event
            uniq_id          int Persons uniq_id
            source_id        int The uniq_id of the Source citated
            clearname        str Persons display name
            eventtype        str type for Event
            edates           DateRange date expression for Event
            date             str date for Event
    '''
    def __init__(self):
        self.label = ''
        self.uniq_id = ''
        self.source_id = None
        self.clearname = ''
        self.eventtype = ''
        self.edates = None
        self.date = ''

    def __str__(self):
        return "{} {}: {} {} '{}'".format(self.label, self.uniq_id, self.source_id or '-', self.eventtype, self.clearname)
