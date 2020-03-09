'''
Created on 5.3.2020

@author: jm
'''
class SourceCypher():
    """ Cypher clauses for Source data access.
    """

    # ------------------------ Cypher fragments ------------------------

    # Select Source from auditted data / researcher's own data
    _match_auditted = "MATCH (s:Source) <-[owner:PASSED]- ()"
    _match_own = "MATCH (s:Source) <-[owner:OWNS|OWNS_OTHER]- ()"

    _sets = """
WITH type(owner) as owner_type, s
    OPTIONAL MATCH (s) -[:NOTE]-> (note)
    OPTIONAL MATCH (s) -[r:REPOSITORY]-> (rep:Repository)
    OPTIONAL MATCH (c:Citation) -[:SOURCE]-> (s)
    OPTIONAL MATCH (c) <-[:CITATION]- (citator)
RETURN owner_type, s as source, collect(DISTINCT note) as notes, 
       collect(DISTINCT [r.medium, rep]) as repositories,
       COUNT(c) AS cit_cnt, COUNT(citator) AS ref_cnt 
ORDER BY toUpper(s.stitle)"""

    _set_selections = """
        WHERE s.stitle CONTAINS $key1 OR s.stitle CONTAINS $key2 
WITH type(owner) as owner_type, s ORDER BY toUpper(s.stitle)
    OPTIONAL MATCH (s) -[:NOTE]-> (note)
    OPTIONAL MATCH (s) -[r:REPOSITORY]-> (rep:Repository)
    OPTIONAL MATCH (c:Citation) -[:SOURCE]-> (s)
    OPTIONAL MATCH (c) <-[:CITATION]- (citator)
RETURN owner_type, s as source, collect(DISTINCT note) as notes, 
       collect(DISTINCT [r.medium, rep]) as repositories,
       COUNT(c) AS cit_cnt, COUNT(citator) AS ref_cnt 
ORDER BY toUpper(s.stitle)"""

    _single_set_selection = """
MATCH (source:Source) <-[:PASSED]- ()
        WHERE ID(source)=$sid
    OPTIONAL MATCH (source) -[r:REPOSITORY]-> (rep:Repository)
    OPTIONAL MATCH (source) -[:NOTE]-> (n)
RETURN type(owner) as owner_type, source, 
    COLLECT(n) AS notes, COLLECT([r.medium,rep]) AS reps"""


    # ------------------------ Cypher clauses ------------------------

    get_auditted_sets = _match_auditted + _sets
    get_own_sets = _match_own + _sets

    get_auditted_set_selections = _match_auditted + _set_selections
    get_own_set_selections = _match_own + _set_selections

    get_auditted_set_single_selection = _match_auditted + _single_set_selection
    get_own_set_single_selection = _match_own + _single_set_selection

    