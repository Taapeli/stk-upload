# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=missing-docstring
# pylint: disable=bad-whitespace
# pylint: disable=trailing-whitespace
# pylint: disable=trailing-newlines
# pylint: disable=too-few-public-methods
# pylint: disable=too-many-branches
# pylint: disable=no-member

from timespan import Person, Event
from timespan import calculate_estimates
from timespan import BIRTH, DEATH, MARRIAGE, BURIAL, BAPTISM
import timespan
timespan.MAX_AGE = 100

def xtest(name,*events):
    return
    p = Person()
    p.events = events

    calculate_estimates(p)
    #print("latest_possible_birth_year=",p.latest_possible_birth_year)
    #print("latest_possible_death_year=",p.latest_possible_death_year)

    print(name)
    print(f"   birth: {p.earliest_possible_birth_year}-{p.latest_possible_birth_year}")
    print(f"   death: {p.earliest_possible_death_year}-{p.latest_possible_death_year}")


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
    print(f"   birth: {p.earliest_possible_birth_year}-{p.latest_possible_birth_year}")
    print(f"   death: {p.earliest_possible_death_year}-{p.latest_possible_death_year}")

    print("p2")
    p = p2
    print(f"   birth: {p.earliest_possible_birth_year}-{p.latest_possible_birth_year}")
    print(f"   death: {p.earliest_possible_death_year}-{p.latest_possible_death_year}")

    print("p3")
    p = p3
    print(f"   birth: {p.earliest_possible_birth_year}-{p.latest_possible_birth_year}")
    print(f"   death: {p.earliest_possible_death_year}-{p.latest_possible_death_year}")


if __name__ == "__main__":
    main()
    
def test_none():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",None),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.earliest_possible_birth_year is None
    assert p1.latest_possible_birth_year is None
    assert p1.earliest_possible_death_year is None
    assert p1.latest_possible_death_year is None
    

def test0():
    p1 = Person()
    p1.events = [
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.earliest_possible_birth_year is None
    assert p1.latest_possible_birth_year is None
    assert p1.earliest_possible_death_year is None
    assert p1.latest_possible_death_year is None
    

def test1():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1900),
        Event(DEATH,"exact",1950),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.earliest_possible_birth_year == 1900
    assert p1.latest_possible_birth_year == 1900
    assert p1.earliest_possible_death_year == 1950
    assert p1.latest_possible_death_year == 1950
    

def test2():
    p1 = Person()
    p1.events = [
        Event("resi","exact",1950),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.earliest_possible_birth_year == 1850
    assert p1.latest_possible_birth_year == 1950
    assert p1.earliest_possible_death_year == 1950
    assert p1.latest_possible_death_year == 2050

def test3():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1900),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.earliest_possible_birth_year == 1900
    assert p1.latest_possible_birth_year == 1900
    assert p1.earliest_possible_death_year == 1900
    assert p1.latest_possible_death_year == 2000
    
def test4():
    p1 = Person()
    p1.events = [
        Event(DEATH,"exact",1900),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.earliest_possible_birth_year == 1800
    assert p1.latest_possible_birth_year == 1900
    assert p1.earliest_possible_death_year == 1900
    assert p1.latest_possible_death_year == 1900
    
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
    assert p2.earliest_possible_birth_year == 1915
    assert p2.latest_possible_birth_year == 1950
    assert p2.earliest_possible_death_year == 1915
    assert p2.latest_possible_death_year == 2050
    
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
    assert p2.earliest_possible_birth_year == 1915
    assert p2.latest_possible_birth_year == 1965
    assert p2.earliest_possible_death_year == 1915
    assert p2.latest_possible_death_year == 2065
    
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
    assert p2.earliest_possible_birth_year == 1915
    assert p2.latest_possible_birth_year == 1965
    assert p2.earliest_possible_death_year == 1915
    assert p2.latest_possible_death_year == 2065

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
    assert p2.earliest_possible_birth_year == 1930
    assert p2.latest_possible_birth_year == 1930
    assert p2.earliest_possible_death_year == 1930
    assert p2.latest_possible_death_year == 2030

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
    assert p2.earliest_possible_birth_year == 1915
    assert p2.latest_possible_birth_year == 1930
    assert p2.earliest_possible_death_year == 1930
    assert p2.latest_possible_death_year == 1930

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
    assert p2.earliest_possible_birth_year == 1930
    assert p2.latest_possible_birth_year == 1965
    assert p2.earliest_possible_death_year == 2030
    assert p2.latest_possible_death_year == 2030


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
    assert p1.earliest_possible_birth_year == 1835
    assert p1.latest_possible_birth_year == 1985
    assert p1.earliest_possible_death_year == 1900
    assert p1.latest_possible_death_year == 2085
    
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
    assert p1.earliest_possible_birth_year == 1935
    assert p1.latest_possible_birth_year == 1985
    assert p1.earliest_possible_death_year == 2000
    assert p1.latest_possible_death_year == 2085
    
    
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
    assert p1.earliest_possible_birth_year == 1885
    assert p1.latest_possible_birth_year == 1935
    assert p1.earliest_possible_death_year == 1950
    assert p1.latest_possible_death_year == 2035
    
    
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
    assert p1.earliest_possible_birth_year == 1885
    assert p1.latest_possible_birth_year == 1935
    assert p1.earliest_possible_death_year == 1950
    assert p1.latest_possible_death_year == 2035
    
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
    assert p1.earliest_possible_birth_year == 1885
    assert p1.latest_possible_birth_year == 1935
    assert p1.earliest_possible_death_year == 1950
    assert p1.latest_possible_death_year == 2035

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
    assert p1.earliest_possible_birth_year == 1885
    assert p1.latest_possible_birth_year == 1985
    assert p1.earliest_possible_death_year == 1950
    assert p1.latest_possible_death_year == 2085

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
    assert p1.earliest_possible_birth_year == 1885
    assert p1.latest_possible_birth_year is None
    assert p1.earliest_possible_death_year == 1950
    assert p1.latest_possible_death_year is None

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
    assert p1.earliest_possible_birth_year == 1885
    assert p1.latest_possible_birth_year == 1985
    assert p1.earliest_possible_death_year == 1950
    assert p1.latest_possible_death_year == 2085

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
    assert p1.earliest_possible_birth_year == 1835
    assert p1.latest_possible_birth_year == 1935
    assert p1.earliest_possible_death_year == 1900
    assert p1.latest_possible_death_year == 2035

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
    assert p1.earliest_possible_birth_year == 1835
    assert p1.latest_possible_birth_year == 1935
    assert p1.earliest_possible_death_year == 1900
    assert p1.latest_possible_death_year == 2035

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
    assert p1.earliest_possible_birth_year is None
    assert p1.latest_possible_birth_year == 1935
    assert p1.earliest_possible_death_year is None
    assert p1.latest_possible_death_year == 2035

def xtest14():
    p1 = Person()
    p1.events = [
        Event(BIRTH,"exact",1950),
        Event(DEATH,"exact",1940),
    ]
    persons = [p1]
    calculate_estimates(persons)
    assert p1.earliest_possible_birth_year == 1950
    assert p1.latest_possible_birth_year == 1950
    assert p1.earliest_possible_death_year == 1940
    assert p1.latest_possible_death_year == 1940

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
    assert p1.earliest_possible_birth_year == 1820
    assert p1.latest_possible_birth_year == 1920
    assert p1.earliest_possible_death_year == 1885
    assert p1.latest_possible_death_year == 2020
