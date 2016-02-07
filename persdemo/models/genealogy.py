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
from py2neo import Graph, Node, Relationship
import logging

graph = Graph()

# ---------------------------------- Funktiot ----------------------------------

def tyhjenna_kanta():
    """ Koko kanta tyhjennetään """
    graph.delete_all()
    
def make_id(prefix, int):
    """ Palautetaan rivinumeroa int vastaava id, esim. 'P00001' """
    return prefix + str(int).zfill(5)

# --------------------------------- Apuluokat ----------------------------------

class User:
    """ Järjestelmän käyttäjä """
    
    _label_ = "User"
    
    def __init__(self, username, name):
        """ Luo uuden käyttäjä-instanssin """
        self.id = username
        self.name = name

    def save(self):
        """ Talletta sen kantaan """
        user = Node(self._label_, uid=self.id, name=self.name)
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
    def __init__(self, id):
        self.id=id
        self.events = []
        return
    
    def make_id(int):
        """ Palautetaan rivinumeroa int vastaava person_id, esim. 'P00001' """
        # TODO: korvaa ohjelmissa Person.make_id(i) --> make_id('P', i)
        return 'P'+str(int).zfill(5)

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
        
        # Henkilö-noodi
        persoona = Node("Person", id=self.id, \
                firstname=self.name.first, lastname=self.name.last)
        if self.occupation:
            persoona.properties["occu"] = self.occupation
        if self.place:
            persoona.properties["place"] = self.place

        if len(self.events) > 0:
            # Luodaan (Person)-->(Event) solmuparit
            for event in self.events:
                # Tapahtuma-noodi
                tapahtuma = Node("Event", id=event.id, type=event.type, \
                        name=event.name, date=event.date)
                osallistui = Relationship(persoona, "OSALLISTUI", tapahtuma)
                graph.create(osallistui)
        else:
            # Henkilö ilman tapahtumaa (näitä ei taida aineistossamme olla)
            graph.create(persoona)
            
        return 
        
    def get_all_persons (self):
        query = """
        MATCH (n:Person) RETURN n LIMIT 10;
        """
        return graph.cypher.execute(query)

    def get_events (self):
        query = """
        MATCH (n:Person) - [:OSALLISTUI] -> (e:Event) WHERE n.id = {pid} RETURN e;
        """
        return graph.cypher.execute(query,  pid=self.id)
    

class Event:
    """ Tapahtuma
        
        Properties:
            id              str event_id esim. "P00001"
            type            esim. "Käräjät"
            name            tapahtuman nimi "käräjäpaikka aika"
            date            str aika
            place           str paikka
     """
    def __init__(self, id, tyyppi):
        self.id=id
        self.type = tyyppi
        return

class Name:
    """ Etu- ja sukunimi, patronyymi sekä nimen alkuperäismuoto
    """
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
    pass

class Note:
    pass

class Refname:
    """
        ( RefName {id, luokka, nimi} ) -[reftype]-> (RefName)
                   luokka = (etu, suku, paikka, ...)
                   reftype = (refnimi, patronyymi, ...)
        Properties:
            id      R00001 ...
            type    in REFTYPES
            name    1st letter capitalized
            refname id points to reference name, ei exists
            reftype which kind of reference refname points to
            is_ref  true, if this is a reference name
            gender  gender 'F', 'M' or ''
            source  points to Source
    """
    # TODO: refname'en on laitettu nyt nimi, pitäisi olla nimen id
    # TODO: source pitäisi olla viite lähdetietoon, nyt sinne on laitettu lähteen nimi

    __REFNAMETYPES__ = ['undef', 'fname', 'lname', 'patro', 'place']
    __REFTYPES__ = ['refname', 'patroname']
    
    def __init__(self, id, tyyppi, nimi):
        self.id=id
        # Nimi alkukirjain isolla, alku- ja loppublankot poistettuna
        self.name = nimi.strip().title()
        if tyyppi in self.__REFNAMETYPES__:
            self.type = tyyppi
        else:
            self.type = self.__REFNAMETYPES__[0]
            logging.warning('Referenssinimen tyyppi ' + tyyppi + \
                            ' hylätty. ' + self.__str__())
        return

    def setref(self, ref_id, reftype):
        if reftype in self.__REFTYPES__:
            self.ref = ref_id
            self.reftype = reftype
        else:
            logging.warning('Referenssinimen viittaus ' + reftype + \
                            ' hylätty. ' + self.__str__())
            
    def __str__(self):
        s = "Refname type:%s '%s'", (self.type, self.name)
        if self.date:
            s += " (kirjattu %s)", (self.date, )
        if self.ref:
            s += " [%s]"
        return s


class Citation:
    pass

class Source:
    pass

class Archieve:
    pass
