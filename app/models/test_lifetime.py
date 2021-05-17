# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=missing-docstring
# pylint: disable=bad-whitespace
# pylint: disable=trailing-whitespace
# pylint: disable=trailing-newlines
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-branches
# pylint: disable=no-member

from lifetime import Event
from lifetime import calculate_estimates
from lifetime import BIRTH, DEATH, MARRIAGE, BURIAL, BAPTISM, MIN, MAX
import lifetime

lifetime.MAX_AGE = 100
lifetime.MAX_BAPTISM_DELAY = 0
lifetime.MAX_BURIAL_DELAY = 0
lifetime.MAX_PARENT_DEATH_CHILD_BIRTH_GAP = 0

class Person(lifetime.Person):
    def __init__(self, pid=None):
        lifetime.Person.__init__(self)
        if pid is None: pid = str(id(self))
        self.pid = pid
    def __str__(self):
        return self.pid

def xtest(name,*events):
    return
    p = Person()
    p.events = events

    calculate_estimates(p)
    #print("birth_high=",p.birth_high)
    #print("death_high=",p.death_high)

    print(name)
    print(f"   birth: {p.birth_low}-{p.birth_high}")
    print(f"   death: {p.death_low}-{p.death_high}")


#-----------------------------------------------

def main():    
    p1 = Person()
    p1.events = [
        #    Event(BIRTH,"exact",1860),
        #    Event(DEATH,"exact",1950),
        #Event("resi","exact",1950),
        #Event(MARRIAGE,"exact",1960),
    ]


    p2 = Person()
    p2.events = [
        #Event("resi","exact",1900),
        #    Event(MARRIAGE,"exact",1960),
    ]

    p3 = Person()
    p3.events = [
        Event("resi","exact",1980),
    ]


    p1.parents = [p2]
    p3.parents = [p2]
    p1.children = []
    p2.children = [p1,p3]

    calculate_estimates([p1,p2,p3])

    print("p1")
    p = p1
    print(f"   birth: {p.birth_low}-{p.birth_high}")
    print(f"   death: {p.death_low}-{p.death_high}")

    print("p2")
    p = p2
    print(f"   birth: {p.birth_low}-{p.birth_high}")
    print(f"   death: {p.death_low}-{p.death_high}")

    print("p3")
    p = p3
    print(f"   birth: {p.birth_low}-{p.birth_high}")
    print(f"   death: {p.death_low}-{p.death_high}")


if __name__ == "__main__":
    main()
    
def test_none():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",None),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.birth_low is MIN
    assert p1.birth_high is MAX
    assert p1.death_low is MIN
    assert p1.death_high is MAX
    

def test0():
    p1 = Person()
    p1.events = [
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.birth_low is MIN
    assert p1.birth_high is MAX
    assert p1.death_low is MIN
    assert p1.death_high is MAX
    

def test1():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1900),
        Event(DEATH,"exact",1950),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.birth_low == 1900
    assert p1.birth_high == 1900
    assert p1.death_low == 1950
    assert p1.death_high == 1950
    

def test2():
    p1 = Person()
    p1.events = [
        Event("resi","exact",1950),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.birth_low == 1850
    assert p1.birth_high == 1950
    assert p1.death_low == 1950
    assert p1.death_high == 2050

def test3():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1900),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.birth_low == 1900
    assert p1.birth_high == 1900
    assert p1.death_low == 1900
    assert p1.death_high == 2000
    
def test4():
    p1 = Person()
    p1.events = [
        Event(DEATH,"exact",1900),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.birth_low == 1800
    assert p1.birth_high == 1900
    assert p1.death_low == 1900
    assert p1.death_high == 1900
    
def test5():
    # p1 is a parent of p2
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1900),
        Event(DEATH,"exact",1950),
    ]
    p2 = Person()
    p2.events = [
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p2.birth_low == 1915
    assert p2.birth_high == 1950
    assert p2.death_low == 1915
    assert p2.death_high == 2050
    
def test6():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1900),
    ]
    p2 = Person()
    p2.events = [
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p2.birth_low == 1915
    assert p2.birth_high == 1965
    assert p2.death_low == 1915
    assert p2.death_high == 2065
    
def test7():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1900),
        Event(DEATH,"exact",1999),
    ]
    p2 = Person()
    p2.events = [
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p2.birth_low == 1915
    assert p2.birth_high == 1965
    assert p2.death_low == 1915
    assert p2.death_high == 2065

def test8():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1900),
        Event(DEATH,"exact",1999),
    ]
    p2 = Person()
    p2.events = [
        Event(BIRTH,"exact",1930),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p2.birth_low == 1930
    assert p2.birth_high == 1930
    assert p2.death_low == 1930
    assert p2.death_high == 2030

def test9():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1900),
        Event(DEATH,"exact",1999),
    ]
    p2 = Person()
    p2.events = [
        Event(DEATH,"exact",1930),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p2.birth_low == 1915
    assert p2.birth_high == 1930
    assert p2.death_low == 1930
    assert p2.death_high == 1930

def test10():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1900),
        Event(DEATH,"exact",1999),
    ]
    p2 = Person()
    p2.events = [
        Event(DEATH,"exact",2030),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p2.birth_low == 1930
    assert p2.birth_high == 1965
    assert p2.death_low == 2030
    assert p2.death_high == 2030


def test11():
    p1 = Person()
    p1.events = [
    ]
    p2 = Person()
    p2.events = [
        Event(DEATH,"exact",2000),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1835
    assert p1.birth_high == 1985
    assert p1.death_low == 1900
    assert p1.death_high == 2085
    
def test12():
    p1 = Person()
    p1.events = [
    ]
    p2 = Person()
    p2.events = [
        Event(BIRTH,"exact",2000),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1935
    assert p1.birth_high == 1985
    assert p1.death_low == 2000
    assert p1.death_high == 2085
    
    
def test13a():
    p1 = Person()
    p1.events = [
    ]
    p2 = Person()
    p2.events = [
        Event(BIRTH,"exact",1950),
        Event(DEATH,"exact",2000),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1885
    assert p1.birth_high == 1935
    assert p1.death_low == 1950
    assert p1.death_high == 2035
    
    
def test13b():
    p1 = Person()
    p1.events = [
    ]
    p2 = Person()
    p2.events = [
        Event(BIRTH,"exact",1950),
        Event(DEATH,"after",2000),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1885
    assert p1.birth_high == 1935
    assert p1.death_low == 1950
    assert p1.death_high == 2035
    
def test13c():
    p1 = Person()
    p1.events = [
    ]
    p2 = Person()
    p2.events = [
        Event(BIRTH,"exact",1950),
        Event(DEATH,"before",2000),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1885
    assert p1.birth_high == 1935
    assert p1.death_low == 1950
    assert p1.death_high == 2035

def test13d():
    p1 = Person()
    p1.events = [
    ]
    p2 = Person()
    p2.events = [
        Event(BIRTH,"after",1950),
        Event(DEATH,"exact",2000),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1885
    assert p1.birth_high == 1985
    assert p1.death_low == 1950
    assert p1.death_high == 2085

def test13f():
    p1 = Person()
    p1.events = [
    ]
    p2 = Person()
    p2.events = [
        Event(BIRTH,"after",1950),
        Event(DEATH,"after",2000),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1885
    assert p1.birth_high is MAX
    assert p1.death_low == 1950
    assert p1.death_high is MAX

def test13g():
    p1 = Person()
    p1.events = [
    ]
    p2 = Person()
    p2.events = [
        Event(BIRTH,"after",1950),
        Event(DEATH,"before",2000),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1885
    assert p1.birth_high == 1985
    assert p1.death_low == 1950
    assert p1.death_high == 2085

def test13h():
    p1 = Person()
    p1.events = [
    ]
    p2 = Person()
    p2.events = [
        Event(BIRTH,"before",1950),
        Event(DEATH,"exact",2000),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1835
    assert p1.birth_high == 1935
    assert p1.death_low == 1900
    assert p1.death_high == 2035

def test13i():
    p1 = Person()
    p1.events = [
    ]
    p2 = Person()
    p2.events = [
        Event(BIRTH,"before",1950),
        Event(DEATH,"after",2000),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1835
    assert p1.birth_high == 1935
    assert p1.death_low == 1900
    assert p1.death_high == 2035

def test13j():
    p1 = Person()
    p1.events = [
    ]
    p2 = Person()
    p2.events = [
        Event(BIRTH,"before",1950),
        Event(DEATH,"before",2000),
    ]
    p1.children = [p2]
    p2.parents = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low is MIN
    assert p1.birth_high == 1935
    assert p1.death_low is MIN
    assert p1.death_high == 2035

def xtest14():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1950),
        Event(DEATH,"exact",1940),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.birth_low == 1950
    assert p1.birth_high == 1950
    assert p1.death_low == 1940
    assert p1.death_high == 1940

def test15():
    p1 = Person()
    p2 = Person()
    p3 = Person()
    p3.events = [
        Event(BIRTH,"exact",1950),
    ]
    persons = [p1,p2,p3]
    p1.children = [p2]
    p2.children = [p3]
    p2.parents = [p1]
    p3.parents = [p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1820
    assert p1.birth_high == 1920
    assert p1.death_low == 1885
    assert p1.death_high == 2020

def test16():
    p1 = Person("p1")
    p1.events = [
    ]
    p2 = Person("p2")
    p2.events = [
        Event(BIRTH,"exact",1900),
        Event(DEATH,"exact",2000),
    ]
    p1.spouses = [p2]
    p2.spouses = [p1]
    persons = [p1,p2]
    calculate_estimates(persons)
    assert p1.birth_low == 1815
    assert p1.birth_high == 1985
    assert p1.death_low == 1915
    assert p1.death_high == 2085
