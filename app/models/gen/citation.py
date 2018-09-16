'''
    Citation class for handling Citation nodes and relations

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from sys import stderr

from models.cypher_gramps import Cypher_citation_w_handle
import shareds
from models.gen.event import Event

class Citation:
    """ Viittaus
            
        Properties:
                handle          
                change
                id               esim. "C0001"
                dateval          str date
                page             str page
                confidence       str confidence
                noteref_hlink    str huomautuksen osoite
                sourceref_hlink  str lähteen osoite
     """
    def __init__(self):
        """ Luo uuden citation-instanssin """
        self.handle = ''
        self.change = 0
        self.id = ''
        self.dateval = ''
        self.page = ''
        self.noteref_hlink = []
        self.sourceref_hlink = ''
        self.sources = []   # For creating display sets
        self.citators = []  # For creating display sets

    def __str__(self):
        return "{} '{}'".format(self.id, self.page)
    
    @staticmethod       
    def get_persons_citations (uniq_id):
        """ Read 'Person -> Event -> Citation' and 'Person -> Citation' paths

            Haetaan henkilön Citationit, suoraan tai välisolmujen kautta
        """
        get_persons_citation_paths = """
match path = (p) -[*]-> (c:Citation) where id(p) = $pid 
with relationships(path) as rel, c
return extract(x IN rel | x.role) as role, 
       extract(x IN rel | endnode(x)) as end"""

#TODO: Roolia ei tarvita?
# ╒════════════════╤════════════════════════════════════════════════════════╕
# │"role"          │"end"                                                   │
# ╞════════════════╪════════════════════════════════════════════════════════╡
# │["Primary",null]│[{"datetype":0,"change":1521882912,"description":"","han│
# │                │dle":"_dd768e76e66620bbff00d54bc8","attr_type":"","id":"│
# │                │E2823","date2":1869087,"type":"Baptism","date1":1869087,│
# │                │"attr_value":""},                                       │
# │                │                 {"handle":"_dd768dca3a62654475a5726dfcd│
# │                │","page":"s. 336 1825 Augusti 29 kaste 27","id":"C1362",│
# │                │"dateval":"","confidence":"2","change":1521882911}]     │
# ├────────────────┼────────────────────────────────────────────────────────┤
# │[null]          │[{"handle":"_dd7686926d946cd18c5642e61e2","id":"C1361","│
# │                │page":"1891 Syyskuu 22","dateval":"","change":1521882215│
# │                │,"confidence":"2"}]                                     │
# └────────────────┴────────────────────────────────────────────────────────┘
        
        result = shareds.driver.session().run(get_persons_citation_paths, 
                                            pid=uniq_id)
        citations = []
        for record in result:
            roles = record['role']
            nodes = record['end']
            c = Citation()
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
                e.eventrole = roles[0]
                c.citators.append(e)

            c.id = cit.id
            c.label = cit.labels.pop()
            c.uniq_id = cit.id
            c.page = cit['page']
            c.confidence = cit['confidence']

            citations.append(c)

        return citations


    @staticmethod       
    def get_source_repo (uniq_id=None):
        """ Read Citation -> Source -> Repository chain
            and optionally Notes.            
            Citation has all data but c.handle

            Voidaan lukea annetun Citationin lähde ja arkisto kannasta
        """

        if uniq_id:
            where = "WHERE ID(c)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
 MATCH (c:Citation) -[r:SOURCE]-> (source:Source) 
    -[p:REPOSITORY]-> (repo:Repository) {0}
 OPTIONAL MATCH (c) -[n:NOTE]-> (note:Note)
   WITH c, r, source, p, repo 
   ORDER BY c.page, note
 RETURN ID(c) AS id, 
    c.dateval AS date,
    c.page AS page,
    c.confidence AS confidence, 
    note.text AS notetext,
    COLLECT(DISTINCT [ID(source), 
             source.stitle, 
             p.medium, 
             ID(repo), 
             repo.rname, 
             repo.type]) AS sources
 """.format(where)
                
        return shareds.driver.session().run(query)
    
    
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
                self.sourceref_hlink = record['id']

    
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
        if self.sourceref_hlink != '':
            print ("Sourceref_hlink: " + self.sourceref_hlink)
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
            if self.sourceref_hlink != '':
                tx.run(Cypher_citation_w_handle.link_source,
                       handle=self.handle, hlink=self.sourceref_hlink)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
        return


class NodeRef():
    ''' Carries data of citating nodes
            label            str Person or Event
            uniq_id          int Persons uniq_id
            clearname        str Persons display name
            eventtype        str type for Event
            edates           DateRange date expression for Event
            date             str date for Event
    '''
    def __init__(self):
        self.label = ''
        self.uniq_id = ''
        self.clearname = ''
        self.eventtype = ''
        self.edates = None
        self.date = ''

    def __str__(self):
        return "{} {} '{}'".format(self.uniq_id, self.eventtype, self.clearname)
