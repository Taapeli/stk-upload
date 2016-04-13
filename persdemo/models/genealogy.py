# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 25.1.2016

"""
Luokkamalli
    ( User {uid, nimi} )

    ( Person {id, gender, norm_name} )    --> (Event)
    ( Event {id, name, aika} )            --> (Place), (Citation), (Name)
    ( Name {id, orig, etu, suku, patro} ) --> (RefName)
    ( Place {id, orig, nimi} )            --> (RefName)
    ( Note {id, teksti, url} )
    ( RefName {id, luokka, nimi} )        -[reftype]-> (RefName)
                   luokka = (etu, suku, paikka, ...)
                   reftype = (refnimi, patronyymi, ...)
    ( Citation {id, nimi, aika} )         --> (Source)
    ( Source {id, nimi, aika} )           --> (Archieve)
    ( Archieve {id, nimi} )
    ( Migration {id, aika} )        -[from]-> (Place), -[to]-> (Place)

"""
from py2neo import Graph, Node, Relationship, authenticate
import logging
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
        
def tyhjenna_kanta():
    """ Koko kanta tyhjennetään """
    logging.info('Tietokanta tyhjennetään!')
    global graph
    graph.delete_all()
    
def make_id(prefix, int):
    """ Palautetaan rivinumeroa int vastaava id, esim. 'P00001' """
    return prefix + str(int).zfill(5)

# --------------------------------- Apuluokat ----------------------------------

class User:
    """ Järjestelmän käyttäjä """
    
    label = "User"
    
    def __init__(self, username, name):
        """ Luo uuden käyttäjä-instanssin """
        self.id = username
        self.name = name

    def save(self):
        """ Talletta sen kantaan """
        user = Node(self.label, uid=self.id, name=self.name)
        graph.create(user)
        return True
    
    def get(self, username):
        """ Pitäisi hakea käyttäjien tiedot kannasta 
            ja palauttaa listan instansseja.
            (Tosin ei pitäisi olla montaa Useria samalla id:llä)
        """
        name='luettu kannasta'
        return ( User(username, name), )
    
    def __str__(self):
        return "User username=" + self.id + ", nimi=" + self.name;

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
                logging.warning('Aika korjattu: %s -> %s' % (id, t))

        t = t.replace('.', '-')
        return t


#  ------------------------ Taapelin Suomikannan luokat ------------------------

class Person:
    """ Henkilötiedot 
        
        Properties:
            id              str person_id esim. "P00001"
            firstnames[]    list of str
            lastname        str
            std_name        esim. "Sukunimi, Etunimi"
            name            Name(etu, suku)
            occupation      str ammatti
            place           str paikka
            events[]        list of Event
    """
    label = "Person"

    def __init__(self, id):
        self.id=id
        self.events = []
    
    def make_id(int_id):
        """ Palautetaan rivinumeroa int vastaava person_id, esim. 'P00001' """
        # TODO: korvaa ohjelmissa Person.make_id(i) --> make_id('P', i)
        return 'P'+str(int_id).zfill(5)

    def save(self):
        """ Tallennus kantaan. Edellytetään, että henkilölle on asetettu:
            - id
            - name = Name(etu, suku)
            Lisäksi tallennetaan valinnaiset tiedot:
            - events[] = (Event(), )
            - occupation
            - place
        """
        # TODO: pitäsi huolehtia, että käytetään entistä tapahtumaa, jos on
        
        global graph
        # Henkilö-noodi
        persoona = Node(self.label, id=self.id, \
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
                tapahtuma = Node(Event.label, id=event.id, type=event.type, \
                        name=event.name, date=event.date)
                osallistui = Relationship(persoona, "OSALLISTUI", tapahtuma)
                graph.create(osallistui)
        else:
            # Henkilö ilman tapahtumaa (näitä ei taida aineistossamme olla)
            graph.create(persoona)
                    
    def get_persons (max=0, pid=None, names=None):
        """ Voidaan lukea henkilöitä tapahtumineen kannasta seuraavasti:
            get_persons()               kaikki
            get_persons(id='P000123')   tietty henkilö id:n mukaan poimittuna
            get_persons(names='And')    henkilöt, joiden sukunimen alku täsmää
            - lisäksi (max=100)         rajaa luettavien henkilöiden määrää
        """
        global graph
        if max > 0:
            qmax = "LIMIT " + str(max)
        else:
            qmax = ""
        if pid:
            where = "WHERE n.id='{}' ".format(pid)
        elif names:
            where = "WHERE n.lastname STARTS WITH '{}' ".format(names)
        else:
            where = ""
        query = "MATCH (n:Person) {0} RETURN n {1};".format(where, qmax)
        return graph.cypher.execute(query)

    def get_person_events (max=0, pid=None, names=None):
        """ Voidaan lukea henkilöitä tapahtumineen kannasta seuraavasti:
            get_persons()               kaikki
            get_persons(id='P000123')   tietty henkilö id:n mukaan poimittuna
            get_persons(names='And')    henkilöt, joiden sukunimen alku täsmää
            - lisäksi (max=100)         rajaa luettavien henkilöiden määrää
        """
        global graph
        if max > 0:
            qmax = "LIMIT " + str(max)
        else:
            qmax = ""
        if pid:
            where = "WHERE n.id='{}' ".format(pid)
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
        MATCH (n:Person) - [:OSALLISTUI] -> (e:Event) WHERE n.id = {pid} RETURN e;
        """
        global graph
        return graph.cypher.execute(query,  pid=self.id)
  
    def key (self):
        "Hakuavain tuplahenkilöiden löytämiseksi sisäänluvussa"
        key =   "{}:{}/{}/:{}".format(self.id, \
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
        key = "{}:{}:{}:{}".format(self.id, 
              self.name.first, self.name.last, self.occupation);
        return key

    def __str__(self):
        s = "Person {}:{} {}".format(self.id, self.firstname, self.lastname)
        return s


class Event:
    """ Tapahtuma
        
        Properties:
            id              str event_id esim. "P00001"
            type            esim. "Käräjät"
            name            tapahtuman nimi "käräjäpaikka aika"
            date            str aika
            place           str paikka
     """
    label = "Event"

    def __init__(self, id, tyyppi):
        self.id=id
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
        ( Refname {id, luokka, nimi} ) -[reftype]-> (Refname)
                   luokka = (etu, suku, paikka, ...)
                   reftype = (refnimi, patronyymi, ...)
        Properties:                                             testiaineistossa
            id      R00001 ...                                  (rivinumerosta)
            type    in REFTYPES                                 ('REFFIRST')
            name    1st letter capitalized                      (Nimi)
            refname the referenced name, if exists              (RefNimi)
            reftype which kind of reference refname points to   ('REFFIRST')
            is_ref  true, if this is a reference name           (On_itse_refnimi)
            gender  gender 'F', 'M' or ''                       (Sukupuoli)
            source  points to Source                            (Lähde)
            
        Note: refnamea ja reftypeä ei talleteta tekstinä, vaan kannassa tehdään
              viittaus tyyppiä reftype ko Refnameen
    """
    # TODO: source pitäisi olla viite lähdetietoon, nyt sinne on laitettu lähteen nimi

    label = "Refname"

    __REFNAMETYPES = ['undef', 'fname', 'lname', 'patro', 'place', 'occu']
    __REFTYPES = ['REFFIRST', 'REFLAST', 'REFPATRO']
    
    def __init__(self, id, type='undef', nimi=None):
        """ Luodaan referenssinimi (id, type, nimi)
        """
        self.id=id
        # Nimi alkukirjain isolla, alku- ja loppublankot poistettuna
        if nimi:
            self.name = nimi.strip().title()
        else:
            self.name = None
        if type in self.__REFNAMETYPES:
            self.type = type
        else:
            self.type = self.__REFNAMETYPES[0]
            logging.warning('Referenssinimen tyyppi ' + type + \
                            ' hylätty. ' + self.__str__())

    def save(self):
        """ Referenssinimen tallennus kantaan. Edellytetään, että sille on asetettu:
            - id (R...)
            - type (fname)
            - name (Nimi)
            - is_ref (On_itse_refnimi)
            Lisäksi tallennetaan valinnaiset tiedot:
            - gender (Sukupuoli='M'/'N'/'')
            - source (Lähde merkkijonona)
            - reference (a:Refname {nimi='Nimi'})
                        -[r:Reftype]->
                        (b:Refname {nimi='RefNimi'})

        """
        # TODO: source pitäisi tallettaa Source-objektina
        
        global graph

        # Pakolliset tiedot
        if self.id == None or self.name == None or self.type == None:
            raise NameError
        
        # Refname-noodi
        instance = Node(self.label, id=self.id, name=self.name, type=self.type)
        if 'gender' in dir(self):
            instance.properties["gender"] = self.gender
        if 'source' in dir(self):
            instance.properties["source"] = self.source
        if 'is_ref' in dir(self):
            instance.properties["is_ref"] = self.is_ref
        logging.debug(self.id + ' tekeillä: ' + self.__str__())
        
        # Luodaan viittaus referenssinimeen, jos on
        if 'refname' in dir(self):
            # Hae kannasta viitattu nimi tai luo uusi nimi
            viitattu = self.getref()
            if viitattu:
                logging.debug(self.id + ' Viitattu löytyi: ' + viitattu.__str__())
                # TODO: Viitattu.is_ref pitää asettaa, jos ei ole päällä
            else:
                id = "R1"+self.id[1:]
                viitattu = Node(self.label, id=id, name=self.refname, 
                                type=self.type, is_ref=True)
                logging.debug(self.id + ' Viitattu luotiin: ' + viitattu.__str__())
                
            # Luo yhteys referoitavaan nimeen
            r = Relationship(instance, self.reftype, viitattu)
            graph.create(r)
        else:
            logging.debug(self.id + ' Viitattua ei ole')
            graph.merge(instance)
        
    def setref(self, refname, reftype):
        """ Laitetaan muistiin, että self viittaa refname'een
        """
        # Ei luoda viittausta itseen
        if self.name == refname:
            self.is_ref = True
            return
        # Viittaustiedot muistiin
        if reftype in self.__REFTYPES:
            self.refname = refname
            self.reftype = reftype
        else:
            logging.warning('Referenssinimen viittaus ' + reftype + \
                        ' hylätty. ' + self.__str__())

    def getref(self):
        """ Haetaan kannasta self:iin liittyvä Refname.
        """
        global graph
        query = """
            MATCH (r:Refname) 
            WHERE r.name ='{0}' AND r.type='{1}' 
            RETURN r;
        """.format(self.refname, self.type)

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
        s = "Refname type:{0} name:'{1}'".format(self.type, self.name)
        if 'gender' in dir(self):
            s += " {0}".format(self.gender)
        if 'is_ref' in dir(self):
            s += " ref=" + str(self.is_ref)
        if 'refname' in dir(self):
            s += " -[{0}]-> (b: name='{1}')".format(self.reftype, self.refname)
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

class UsedIds:
    """ Last used ids
        
        Properties:
            personid             00001 ...
            eventid              00001 ...
            referencenameid      00001 ...
    """

    label = "UsedIds"

    def __init__(self):
        self.personid = 1
        self.eventid = 1
        self.referencenameid = 1

    def get_used_ids(self):
        """ Fetch last used ids from the database.
        """
        global graph
        query = """
            MATCH (n:UsedIds) 
            RETURN n;
        """

        return graph.cypher.execute(query)

    def set_init_values(self):
        """ Set init values to the database.
        """
        global graph

        init_values = Node(self.label,\
                personid=self.personid,\
                eventid=self.eventid,\
                referencenameid=self.referencenameid)

        graph.create(init_values)

    def get_new_id(self, idtype):
        """ Update last used id to the database.
        """
        global graph

        if idtype == "personid":
            setstring = "SET n.personid = {}".format(self.personid)
            id = make_id('P', self.personid)
            self.personid += 1
        elif idtype == "eventid":
            setstring = "SET n.eventid = {}".format(self.eventid)
            id = make_id('E', self.eventid)
            self.eventid += 1
        elif idtype == "referencenameid":
            setstring = "SET n.referencenameid = {}".format(self.referencenameid)
            id = make_id('R', self.referencenameid)
            self.referencenameid += 1

        query = """
            MATCH (n:UsedIds) 
            {}
            RETURN n;
        """.format(setstring)

        graph.cypher.execute(query)
        return id

