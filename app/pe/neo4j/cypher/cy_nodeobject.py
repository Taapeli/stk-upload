'''
Created on 11.8.2023

@author: jm
'''

class CypherNodeObject():
    """
        Clauses for undefined Node types.
    """

    # Input: $batch_id, object $label
    # Output: vars like [["attr_description", "⁋val1⁋"], ["attr_copyright", "⁋val2⁋"]]
    get_gramps_attributes = """
MATCH (root) --> (obj) WHERE $label IN labels(obj)
WITH obj, REDUCE(l = [], x IN KEYS(obj) |
        CASE WHEN x STARTS WITH "attr_" 
        THEN l + [x] ELSE l END
    ) AS attrs
    WHERE SIZE(attrs) > 0
RETURN [ x IN attrs | [x] + obj[x] ] AS vars LIMIT 100
"""

    # Experimental
    list_gramps_attributes_of_latest_batch = """
MATCH (b:Root) WITH b ORDER BY b.id DESC LIMIT 1
MATCH (b) --> (n) 
    WITH b, n, //KEYS(n) AS prop,
        REDUCE(l = [], x IN KEYS(n) 
                | CASE WHEN x STARTS WITH "attr_" 
                    THEN l + [x] 
                    ELSE l END) AS attrs
    WHERE SIZE(attrs) > 0
RETURN n.id, [ x IN attrs | [x] + n[x] ] AS li LIMIT 25
"""
