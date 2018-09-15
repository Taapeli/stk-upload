'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from sys import stderr

from models.cypher_gramps import Cypher_citation_w_handle
import shareds

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
    
    
    @staticmethod       
    def get_source_repo (uniq_id=None):
        """ Read Citation -> Source -> Repository chain
            and optionally Notes.            
            Citation has all data but c.handle

            Voidaan lukea viittauksen lähde ja arkisto kannasta
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
