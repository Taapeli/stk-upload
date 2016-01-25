# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 25.1.2016

"""
Luokkamalli
    ( User {uid, nimi} )
    
    ( Person {id, gender} )         --> (Event)
    ( Event {id, name, aika} )      --> (Place), (Citation)
    ( Name {id, orig, etu, suku, patro} ) --> (RefName)
    ( Place {id, orig, nimi} )      --> (RefName), -[ylempi]-> (Place)
    ( Note {id, teksti, url} )
    ( RefName {id, luokka, nimi} )  luokka = (etu, suku, paikka, ...)
    ( Citation {id, nimi, aika} )   --> (Source)
    ( Source {id, nimi, aika} )     --> (Archieve)
    ( Archieve {id, nimi} )
    ( Migration {id, aika} )        -[from] (Paikka), -[to]-> (Paikka)

"""
from py2neo import Graph, Node, Relationship
graph = Graph()

class User:
    """ Järjestelmän käyttäjä """
    
    _label = "User"
    
    def __init__(self, username, name):
        """ Luo uuden käyttäjä-instanssin """
        self.id = username
        self.name = name

    def save(self):
        """ Talletta sen kantaan """
        user = Node(self._label, uid=self.id, name=self.name)
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


class Person:
    """ Henkilötiedot """
    def __init__(self, id):
        self.id=id
        return

class Event:
    pass

class Name:
    """ Etu- ja sukunimi, patronyymi sekä nimen alkuperäismuoto
    """
    etu = ""
    suku = ""
    
    def __str__(self):
        s = "Nimi %s, %s", (self.suku, self.etu)
        if self.pvm:
            s += " (kirjattu %s)", (self.pvm, )
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
