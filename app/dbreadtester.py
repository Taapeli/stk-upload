'''
Created on 27.7.2020

@author: jm
'''
user='neo4j'
passwd='2000Neo4j'

from neo4j import GraphDatabase
import logging

def is_neo_40():
    """Check, if neo4j driver is Neo4j versio 4.0 compatible"""
    with open("../requirements.txt") as f:
        for line in f.read().splitlines():
            key, ver = line.split('==')
            if key == 'neo4j':
                print(f'Neo4j driver version {line}')
                return ver[:3] >= "1.7"
    return False

def dr_get_place_list_fw(driver):
    ''' Read place list from given start point
    '''
    with driver.session(default_access_mode='READ') as session: 
        query = """
MATCH (b:Batch) -[:OWNS]-> (place:Place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
WHERE b.user = $user AND name.name >= $fw
RETURN place, name ORDER BY name.name LIMIT $limit"""
        result = session.run(query, user='juha', fw='', limit=5, lang='fi')

        for record in result:
            print('\t',record['place']['id'], record['name']['name'])
        print(f'done read')

    with driver.session(default_access_mode='WRITE') as session: 
        update_query = """
MATCH (b:Batch) -[:OWNS]-> (place:Place) -[:NAME_LANG {lang:$lang}]-> (name:Place_name)
WHERE b.user = $user AND name.name >= $fw
WITH name ORDER BY name.name LIMIT $limit
    SET name.prefix = $pre"""
        result = session.run(update_query, user='juha', fw='', limit=2, lang='fi', pre="von")
        counters = result.consume().counters
        print(f'done {counters}')

if __name__ == '__main__':
    neo4j_log = logging.getLogger("neo4j.bolt")
    neo4j_log.setLevel(logging.WARNING)

    neo4version = is_neo_40()
    print('Using neo4j 4.0 version?', neo4version)

#     shareds.app.config.from_pyfile('config.py')
#     uri = app.config['NEO4J_URI']
#     auth = (app.config['NEO4J_USERNAME'], app.config['NEO4J_PASSWORD']),

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=(user,passwd),
                                  connection_timeout=15, encrypted=False)

    dr_get_place_list_fw(driver)


