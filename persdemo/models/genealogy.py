# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 25.1.2016

"""
Luokkamalli
    ( User {uid, nimi} )

    ( Person {oid, gender, norm_name} )    --> (Event)
    ( Event {oid, name, aika} )            --> (Place), (Citation), (Name)
    ( Name {oid, orig, etu, suku, patro} ) --> (RefName)
    ( Place {oid, orig, nimi} )            --> (RefName)
    ( Note {oid, teksti, url} )
    ( RefName {oid, luokka, nimi} )        -[reftype]-> (RefName)
                   luokka = (etu, suku, paikka, ...)
                   reftype = (refnimi, patronyymi, ...)
    ( Citation {oid, nimi, aika} )         --> (Source)
    ( Source {oid, nimi, aika} )           --> (Archieve)
    ( Archieve {oid, nimi} )
    ( Migration {oid, aika} )        -[from]-> (Place), -[to]-> (Place)

"""
from py2neo import Graph, Node, Relationship, authenticate
import logging
import sys
import instance.config as dbconf      # Tietokannan tiedot

# -------------------------- Globaalit muuttujat -------------------------

graph = Graph()

# ---------------------------------- Funktiot ----------------------------------

def connect_db():
    """ 
        genelogy-paketin tarvitsema tietokantayhteys 
    """
    global graph

    #logging.debug("-- dbconf = {}".format(dir(dbconf)))
    if 'graph' in globals():
        print ("connect_db - already done")
    elif 'DB_HOST_PORT' in dir(dbconf):
        print ("connect_db - server {}".format(dbconf.DB_HOST_PORT))
        authenticate(dbconf.DB_HOST_PORT, dbconf.DB_USER, dbconf.DB_AUTH)
        graph = Graph('http://{0}/db/data/'.format(dbconf.DB_HOST_PORT))
    else:
        print ("connect_db - default local")
        graph = Graph()

    # Palautetaan tietokannan sijainnin hostname
    return graph.uri.host
        
def alusta_kanta():
    """ Koko kanta tyhjennetään """
    logging.info('Tietokanta tyhjennetään!')
    
    global graph
    graph.delete_all()

    sch = graph.schema
    
    # Poistetaan vanhat rajoitteet ja indeksit
    for uv in sch.get_uniqueness_constraints('Refname'):
        try:
            sch.drop_uniqueness_constraint('Refname', uv)
        except:
            logging.warning("drop_uniqueness_constraint ei onnistunut:", 
                sys.exc_info()[0])
    for iv in sch.get_indexes('Refname'):
        try:
            sch.drop_index('Refname', iv)
        except:
            logging.warning("drop_index ei onnistunut:", sys.exc_info()[0])

    # Luodaan Refname:n rajoitteet ja indeksit    
    refname_uniq = ["oid", "name"]
    refname_index = ["reftype"]
    for u in refname_uniq:
        sch.create_uniqueness_constraint("Refname", u)
    for i in refname_index:
        sch.create_index("Refname", i)

    
def get_new_oid():
    """ Fetch a new object oid from the database. All types of objects get
        their oid from a common series of numbers 1,2,3, ...
        
        Last used oid is in the node :NextId, which is created if needed.
        NOTE: If you delete node :NextId, the numbering starts from 1 again!
    """
    # Fetch and update last used 'oid + 1' from the database

    global graph
    query = """
        MERGE (n:NextId)
        ON CREATE SET n.nextid=1
        ON MATCH SET n.nextid = n.nextid + 1
        RETURN n.nextid
    """
    return graph.cypher.execute(query).one

# --------------------------------- Apuluokat ----------------------------------

class User:
    """ Järjestelmän käyttäjä """
    
    label = "User"
    
    def __init__(self, username, name):
        """ Luo uuden käyttäjä-instanssin """
        self.oid = username
        self.name = name

    def save(self):
        """ Talletta sen kantaan """
        user = Node(self.label, uid=self.oid, name=self.name)
        graph.create(user)
        return True
    
    def get(self, username):
        """ Pitäisi hakea käyttäjien tiedot kannasta 
            ja palauttaa listan instansseja.
            (Tosin ei pitäisi olla montaa Useria samalla oid:llä)
        """
        name='luettu kannasta'
        return ( User(username, name), )
    
    def __str__(self):
        return "User username=" + self.oid + ", nimi=" + self.name;

class Date():
    """ Päivämäärän muuntofunktioita """
    def range_str(aikamaare):
        """ Karkea aikamäären siivous, palauttaa merkkijonon
        
            Aika esim. '1666.02.20-22' muunnetaan muotoon '1666-02-20 … 22':
            * Tekstin jakaminen sarakkeisiin käyttäen välimerkkiä ”-” 
              tai ”,” (kentät tekstimuotoiltuna)
            * Päivämäärän muotoilu ISO-muotoon vaihtamalla erottimet 
              ”.” viivaksi
         """
        t = aikamaare.replace('-','|').replace(',','|').replace('.', '-')
        if '|' in t:
            osat = t.split('|')
            # osat[0] olkoon tapahtuman 'virallinen' päivämäärä
            t = '%s … %s' % (osat[0], osat[-1])
            if len(osat) > 2:
                logging.warning('Aika korjattu: {} -> {}'.format(aikamaare, t))

        t = t.replace('.', '-')
        return t


#  ------------------------ Taapelin Suomikannan luokat ------------------------

class Person:
    """ Henkilötiedot 
        
        Properties:
            oid             str person_id esim. 123
            firstnames[]    list of str
            lastname        str
            std_name        esim. "Sukunimi, Etunimi"
            name            Name(etu, suku)
            occupation      str ammatti
            place           str paikka
            events[]        list of Event
    """
    label = "Person"

    def __init__(self, oid):
        self.oid=oid
        self.events = []
    
    def save(self):
        """ Tallennus kantaan. Edellytetään, että henkilölle on asetettu:
            - oid
            - name = Name(etu, suku)
            Lisäksi tallennetaan valinnaiset tiedot:
            - events[] = (Event(), )
            - occupation
            - place
        """
        # TODO: pitäsi huolehtia, että käytetään entistä tapahtumaa, jos on
        
        global graph
        # Henkilö-noodi
        persoona = Node(self.label, oid=self.oid, \
                firstname=self.name.first, lastname=self.name.last)
        if self.occupation:
            persoona.properties["occu"] = self.occupation
        if self.place:
            persoona.properties["place"] = self.place
            
        persoona.properties["key"] = self.key()

        if len(self.events) > 0:
            # Luodaan (Person)-->(Event) solmuparit
            for event in self.events:
                # Tapahtuma-noodi
                tapahtuma = Node(Event.label, oid=event.oid, type=event.type, \
                        name=event.name, date=event.date)
                osallistui = Relationship(persoona, "OSALLISTUI", tapahtuma)
                graph.create(osallistui)
        else:
            # Henkilö ilman tapahtumaa (näitä ei taida aineistossamme olla)
            graph.create(persoona)
                    
    def get_persons (max=0, pid=None, names=None):
        """ Voidaan lukea henkilöitä tapahtumineen kannasta seuraavasti:
            get_persons()               kaikki
            get_persons(oid=123)        tietty henkilö oid:n mukaan poimittuna
            get_persons(names='And')    henkilöt, joiden sukunimen alku täsmää
            - lisäksi (max=100)         rajaa luettavien henkilöiden määrää
        """
        global graph
        if max > 0:
            qmax = "LIMIT " + str(max)
        else:
            qmax = ""
        if pid:
            where = "WHERE n.oid='{}' ".format(pid)
        elif names:
            where = "WHERE n.lastname STARTS WITH '{}' ".format(names)
        else:
            where = ""
        query = "MATCH (n:Person) {0} RETURN n {1};".format(where, qmax)
        return graph.cypher.execute(query)

    def get_person_events (max=0, pid=None, names=None):
        """ Voidaan lukea henkilöitä tapahtumineen kannasta seuraavasti:
            get_persons()               kaikki
            get_persons(oid=123)        tietty henkilö oid:n mukaan poimittuna
            get_persons(names='And')    henkilöt, joiden sukunimen alku täsmää
            - lisäksi (max=100)         rajaa luettavien henkilöiden määrää
        """
        global graph
        if max > 0:
            qmax = "LIMIT " + str(max)
        else:
            qmax = ""
        if pid:
            where = "WHERE n.oid='{}' ".format(pid)
        elif names:
            where = "WHERE n.lastname STARTS WITH '{}' ".format(names)
        else:
            where = ""
        query = """
            MATCH (n:Person) {0}  
            OPTIONAL MATCH (n)-->(e) 
            RETURN n, COLLECT(e) {1};""".format(where, qmax)
        return graph.cypher.execute(query)

    def get_events (self):
        query = """
        MATCH (n:Person) - [:OSALLISTUI] -> (e:Event) WHERE n.oid = {pid} RETURN e;
        """
        global graph
        return graph.cypher.execute(query,  pid=self.oid)
  
    def key (self):
        "Hakuavain tuplahenkilöiden löytämiseksi sisäänluvussa"
        key =   "{}:{}/{}/:{}".format(self.oid, \
                self.name.first, self.name.last, self.occupation)
        return key

    def join_persons(self, others):
        """
        Päähenkilöön self yhdistetään henkilöiden others tiedot ja tapahtumat
        """
        othersList = ""
        for i in others:
            otherslist.append(str(i) + " ")
        logging.debug("Yhdistetään henkilöön {} henkilöt {}".format(str(self), othersList))
        pass
    
    # Testi5
    def key (self):
        key = "{}:{}:{}:{}".format(self.oid, 
              self.name.first, self.name.last, self.occupation);
        return key

    def __str__(self):
        s = "Person {}:{} {}".format(self.oid, self.firstname, self.lastname)
        return s


class Event:
    """ Tapahtuma
        
        Properties:
            oid             str event_id esim. 1234
            type            esim. "Käräjät"
            name            tapahtuman nimi "käräjäpaikka aika"
            date            str aika
            place           str paikka
     """
    label = "Event"

    def __init__(self, oid, tyyppi):
        self.oid=oid
        self.type = tyyppi


class Name:
    """ Etu- ja sukunimi, patronyymi sekä nimen alkuperäismuoto
    """
    label = "Name"

    def __init__(self, etu, suku):
        if etu == '': 
            self.first = 'N'
        else:
            self.first = etu

        if suku == '': 
            self.last = 'N'
        else:
            self.last = suku

        if suku == '': suku = 'N'

    def __str__(self):
        s = "Name %s, %s", (self.last, self.first)
        if self.date:
            s += " (kirjattu %s)", (self.date, )
        if self.ref:
            s += " [%s]"
        return s

class Place:
    label = "Place"

    pass

class Note:
    label = "Note"

    pass

class Refname:
    """
        ( Refname {oid, nimi} ) -[reftype]-> (Refname)
                   reftype = (etunimi, sukunimi, patronyymi)

        Properties:                                             input source
            oid     1, 2 ...                                    (created in save())
            name    1st letter capitalized                      (Nimi)
            refname * the std name referenced, if exists        (RefNimi)
            reftype * which kind of reference refname points to ('REFFIRST')
            gender  gender 'F', 'M' or ''                       (Sukupuoli)
            source  points to Source                            (Lähde)
            
        * Note: refnamea ja reftypeä ei talleteta tekstinä, vaan kannassa tehdään
                viittaus tyyppiä reftype ko Refname-olioon
    """
    # TODO: source pitäisi olla viite lähdetietoon, nyt sinne on laitettu lähteen nimi

    label = "Refname"
    __REFTYPES = ['REFFIRST', 'REFLAST', 'REFPATRO']

#   Type-property poistettu tarpeettomana. Esim. samasta nimestä "Persson" voisi
#   olla linkki REFLAST nimeen "Pekanpoika" ja REFPATRO nimeen "Pekka".
#   Ei tarvita useita soluja.
#   __REFNAMETYPES = ['undef', 'fname', 'lname', 'patro', 'place', 'occu']

    def __init__(self, nimi):
        """ Luodaan referenssinimi (type, nimi)
            Nimi talletetaan alkukirjain isolla, alku- ja loppublankot poistettuna
        """
        if nimi:
            self.name = nimi.strip().title()
        else:
            self.name = None

    def save(self):
        """ Referenssinimen tallennus kantaan. Edellytetään, että sille on asetettu:
            - name (Nimi)
            Tunniste luodaan tai käytetään sitä joka löytyi kannasta
            - oid (int)
            Lisäksi tallennetaan valinnaiset tiedot:
            - gender (Sukupuoli='M'/'N'/'')
            - source (Lähde merkkijonona)
            - reference 
              (a:Refname {nimi='Nimi'}) -[r:Reftype]-> (b:Refname {nimi='RefNimi'})
        """
        # TODO: source pitäisi tallettaa Source-objektina
        
        global graph

        # Pakolliset tiedot
        if self.name == None:
            raise NameError
            
        # Onko refnimi jo kannassa?
        self.oid = self.find_refname_id()
        
        if self.oid == None:
            self.oid = get_new_oid()
            logging.debug('{} tekeillä uusi {}'.format(self.oid, str(self)))
        else:
            logging.debug('{} päivitetään vanhaa EI TOIMI {}'.format(self.oid, str(self)))

        # Luodaan Refname-noodi
        instance = Node(self.label, name=self.name)
        if self.oid:
            instance.properties["oid"] = self.oid
        else:
            raise ValueError("Pakollinen tieto 'oid' puuttuu")

        if 'gender' in dir(self):
            instance.properties["gender"] = self.gender
        if 'source' in dir(self):
            instance.properties["source"] = self.source

        # Luodaan viittaus referenssinimeen, jos on
        if 'refname' in dir(self):
            # Hae kannasta viitattu nimi tai luo uusi nimi
            viitattu = self.find_the_refname()
            if viitattu:
                logging.debug('{} Viitattu löytyi: {}'.format(self.oid, str(viitattu)))
            else:
                vid = get_new_oid()
                viitattu = Node(self.label, oid=vid, name=self.refname)
                logging.debug('{} Viitattu luodaan: {}'.format(self.oid, str(viitattu)))
                
            # Luo yhteys referoitavaan nimeen
            r = Relationship(instance, self.reftype, viitattu)
            graph.create(r)
        else:
            logging.debug('{} Viitattua ei ole'.format(self.oid))
            graph.merge(instance)

    def find_the_refname(self):
        """ Haetaan kannasta self:istä viitattu Refname.
        """
        global graph
        query = """
            MATCH (:Refname)-[:{1}]->(p:Refname) 
            WHERE p.name ='{0}' 
            RETURN p;
        """.format(self.refname, self.reftype)

        return graph.cypher.execute(query).one

    def mark_reference(self, refname, reftype):
        """ Laitetaan muistiin, että self viittaa refname'een
        """
        # Ei luoda viittausta itseen
        if self.name == refname:
#            self.is_ref = True
            return
        # Viittaustiedot muistiin
        if reftype in self.__REFTYPES:
            self.refname = refname
            self.reftype = reftype
        else:
            logging.warning('Referenssinimen viittaus {} hylätty. '.format(reftype, str(self)))

    def find_refname_id(self):
        """ Etsitään kannasta, onko tämä referenssinimi siellä.
            Palautetaan ko oid
        """
        query = """
            MATCH (a:Refname) 
            WHERE a.name='{}' 
            RETURN a.oid;
            """.format(self.name)
        return graph.cypher.execute(query).one

    def getrefnames():
        """ Haetaan kannasta kaikki Refnamet 
            Palautetaan Refname-olioita, johon on haettu myös mahdollisen
            viitatun referenssinimen nimi ja tyyppi.
        """
        global graph
        query = """
            MATCH (n:Refname)
            OPTIONAL MATCH (n:Refname)-[r]->(m)
            RETURN n,r,m;
        """
        return graph.cypher.execute(query)

    def __str__(self):
        s = "({}:Refname {}name='{}'".format(self.oid, '{', self.name)
        if 'gender' in dir(self):
            s += " {}".format(self.gender)
        if 'is_ref' in dir(self):
            s += " ref=" + str(self.is_ref)
        if 'refname' in dir(self):
            s += "{}) -[:{}]-> (name='{}')".format('}', self.reftype, self.refname)
        return s


class Citation:
    label = "Citation"

    pass

class Source:
    label = "Source"

    pass

class Archieve:
    label = "Archieve"

    pass
