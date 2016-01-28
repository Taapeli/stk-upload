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

def tyhjenna_kanta():
    """ Koko kanta tyhjennetään """
    graph.delete_all()
    

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
    """ Henkilötiedot """
    def __init__(self, id):
        self.id=id
        self.events = []
        return
    
    def make_id(self, i):
        """ Muodostetaan rivinumeroa vastaava person_id """
        return 'P%06d' % i

class Event:
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
            self.last = etu

        if suku == '': suku = 'N'


    def __str__(self):
        s = "Name %s, %s", (self.last, self.first)
        if self.date:
            s += " (kirjattu %s)", (self.date, )
        if ref:
            s += " [%s]"
        return s
    pass

class Place:
    pass

class Note:
    pass

class Refname:
    pass

class Citation:
    pass

class Source:
    pass

class Archieve:
    pass
