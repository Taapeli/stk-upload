'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from sys import stderr


class Citation:
    """ Viittaus
            
        Properties:
                handle          
                change
                id               esim. "C0001"
                confidence       str confidence
                noteref_hlink    str huomautuksen osoite
                sourceref_hlink  str lähteen osoite
     """

    def __init__(self):
        """ Luo uuden citation-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        self.noteref_hlink = ''
        self.sourceref_hlink = ''

    
    @staticmethod       
    def get_total():
        """ Tulostaa lähteiden määrän tietokannassa """
        
        global session
                
        query = """
            MATCH (c:Citation) RETURN COUNT(c)
            """
        results =  session.run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Citation*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Confidence: " + self.confidence)
        if self.noteref_hlink != '':
            print ("Noteref_hlink: " + self.noteref_hlink)
        if self.sourceref_hlink != '':
            print ("Sourceref_hlink: " + self.sourceref_hlink)
        return True


    def save(self):
        """ Tallettaa sen kantaan """

        global session

        try:
            # Create a new Citation node
            query = """
                CREATE (n:Citation) 
                SET n.gramps_handle='{}', 
                    n.change='{}', 
                    n.id='{}', 
                    n.confidence='{}'
                """.format(self.handle, self.change, self.id, self.confidence)
                
            session.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Note node
            if self.noteref_hlink != '':
                query = """
                    MATCH (n:Citation) WHERE n.gramps_handle='{}'
                    MATCH (m:Note) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:NOTE]->(m)
                     """.format(self.handle, self.noteref_hlink)
                                 
                session.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:   
            # Make relation to the Source node
            if self.sourceref_hlink != '':
                query = """
                    MATCH (n:Citation) WHERE n.gramps_handle='{}'
                    MATCH (m:Source) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:SOURCE]->(m)
                     """.format(self.handle, self.sourceref_hlink)
                                 
                session.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
        return
    

class Repository:
    """ Arkisto
            
        Properties:
                handle          
                change
                id              esim. "R0001"
                rname           str arkiston nimi
                type            str arkiston tyyppi

     """

    def __init__(self):
        """ Luo uuden repository-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        
    
    @staticmethod       
    def get_repositories():
        """ Luetaan kaikki arkistot """
        
        global session
                
        query = """
            MATCH (repo:Repository) RETURN repo
            """
        return  session.run(query)
    
    
    @staticmethod       
    def get_repository(rname):
        """ Luetaan arkiston handle """
        
        global session
                
        query = """
            MATCH (repo:Repository) WHERE repo.rname='{}'
                RETURN repo
            """.format(rname)
        return  session.run(query)
                
    
    @staticmethod       
    def get_total():
        """ Tulostaa arkistojen määrän tietokannassa """
        
        global session
                
        query = """
            MATCH (r:Repository) RETURN COUNT(r)
            """
        results =  session.run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Repository*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Rname: " + self.rname)
        print ("Type: " + self.type)
        return True


    def save(self):
        """ Tallettaa sen kantaan """

        global session

        try:
            query = """
                CREATE (r:Repository) 
                SET r.gramps_handle='{}', 
                    r.change='{}', 
                    r.id='{}', 
                    r.rname='{}', 
                    r.type='{}'
                """.format(self.handle, self.change, self.id, self.rname, self.type)
                
            session.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
        return


class Source:
    """ Lähde
            
        Properties:
                handle          
                change
                id              esim. "S0001"
                stitle          str lähteen otsikko
                noteref_hlink   str huomautuksen osoite
                reporef_hlink   str arkiston osoite
                reporef_medium  str arkiston laatu, esim. "Book"
     """

    def __init__(self):
        """ Luo uuden source-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        self.stitle = ''
        self.noteref_hlink = ''
        self.reporef_hlink = ''
        self.reporef_medium = ''
        
    
    @staticmethod       
    def get_sources(repository_handle):
        """ Luetaan kaikki arkiston lähteet """
        
        global session
                
        query = """
            MATCH (source:Source)-[r:REPOSITORY]->(repo:Repository) 
                WHERE repo.gramps_handle='{}' 
                RETURN r.medium AS medium, source
            """.format(repository_handle)
        return  session.run(query)
        
    
    @staticmethod       
    def get_total():
        """ Tulostaa lähteiden määrän tietokannassa """
        
        global session
                
        query = """
            MATCH (s:Source) RETURN COUNT(s)
            """
        results =  session.run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Source*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        if self.stitle != '':
            print ("Stitle: " + self.stitle)
        if self.noteref_hlink != '':
            print ("Noteref_hlink: " + self.noteref_hlink)
        if self.reporef_hlink != '':
            print ("Reporef_hlink: " + self.reporef_hlink)
        return True
        

    def save(self):
        """ Tallettaa sen kantaan """

        global session

        try:
            query = """
                CREATE (s:Source) 
                SET s.gramps_handle='{}', 
                    s.change='{}', 
                    s.id='{}', 
                    s.stitle='{}'
                """.format(self.handle, self.change, self.id, self.stitle)
                
            session.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
 
        # Make relation to the Note node
        if self.noteref_hlink != '':
            try:
                query = """
                    MATCH (n:Source) WHERE n.gramps_handle='{}'
                    MATCH (m:Note) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:NOTE]->(m)
                     """.format(self.handle, self.noteref_hlink)
                                 
                session.run(query)
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
   
        # Make relation to the Repository node
        if self.reporef_hlink != '':
            try:
                query = """
                    MATCH (n:Source) WHERE n.gramps_handle='{}'
                    MATCH (m:Repository) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:REPOSITORY]->(m)
                     """.format(self.handle, self.reporef_hlink)
                                 
                session.run(query)
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
                
            # Set the medium data of the Source node
            try:
                query = """
                    MATCH (n:Source)-[r:REPOSITORY]->(m) 
                        WHERE n.gramps_handle='{}'
                    SET r.medium='{}'
                     """.format(self.handle, self.reporef_medium)
                                 
                session.run(query)
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
                
        return

