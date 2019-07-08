#!/usr/bin/env python
import argparse
import traceback
from neo4j import GraphDatabase
from models.gen.event import Event
import shareds

# https://neo4j.com/developer/kb/fulltext-search-in-neo4j/
# https://neo4j.com/docs/cypher-manual/3.5/schema/index/#schema-index-fulltext-search
# http://lucene.apache.org/core/5_5_0/queryparser/org/apache/lucene/queryparser/classic/package-summary.html#package.description
#
# Requires Neo4j 3.5 or later

neo4j_uri = shareds.app.config.get("NEO4J_URI")
neo4j_username = shareds.app.config.get("NEO4J_USERNAME")
neo4j_password = shareds.app.config.get("NEO4J_PASSWORD")

neo4j_driver = GraphDatabase.driver(
        neo4j_uri, 
        auth = (neo4j_username,neo4j_password), 
        connection_timeout = 15)

def run(cypher,callback=None,**kwargs):
    try:
        res = neo4j_driver.session().run(cypher, kwargs)
        n = 0
        reslist = list(res)
        count = len(reslist)
        for rec in reslist:
            n += 1
            if callback: callback(n,count,rec)
        return n
    except:
        traceback.print_exc()
        raise

def create_index(args):
    run("""
        CALL db.index.fulltext.createNodeIndex(
        "personIndex",["Person"],["searchkey"])
    """)   

def drop_index(args):
    run("CALL db.index.fulltext.drop('personIndex')") 

def list_indexes(args):
    run("CALL db.indexes",callback=print)

def list_batches(args):
    id = 'id'
    user = 'user'
    file = 'file'
    status = 'status'
    print(f"{id:14s} {user:16s} {file:60s} {status}")
    run("match (b:Batch) return b",callback=list_batch)

def list_batch(rec):
    batch = rec.get('b')
    file = batch.get('file')
    id = batch.get('id')
    user = batch.get('user')
    status = batch.get('status')
    print(f"{id:14s} {user:16s} {file:60s} {status}")

def sanitize(name):
    name = (name
    .replace("'","_")
    .replace("/","_")
    .replace("[","_")
    .replace("]","_")
    .replace("(","_")
    .replace(")","_")
    .replace("?","_")
    .replace("*","_")
    .replace(":","_"))
    return name
    
def generate_searchkey1(n,count,rec):   
    """
    generates searchkey1 for all persons
    """
    keys = []
    pid = rec.get('pid')
    refnames = rec.get('refnames')
    for (rn,bn) in refnames:
        if rn is None or bn is None: continue
        if bn.get('use') == 'firstname': 
            fname = rn.get('name')
            if fname: 
                fname = sanitize(fname)
                for n in fname.split(): keys.append("G"+n)
        if bn.get('use') == 'surname': 
            sname = rn.get('name')
            if sname: 
                sname = sanitize(sname)
                for n in sname.split(): keys.append("L"+n)
        if bn.get('use') == 'patronyme': 
            patronyme = rn.get('name')
            if patronyme: 
                patronyme = sanitize(patronyme)
                keys.append("X"+patronyme)
    for e,pl in rec.get('events'):
        if e is None: continue
        event = Event.from_node(e)
        etype = event.type
        if etype not in {'Birth','Death'}: continue
        edate = event.date
        if pl: 
            eplace = pl.get('pname')
        else:
            eplace = ""
        if etype: 
            etype = etype.replace("'","_")
            if edate:
                edate = str(edate) 
                keys.append(f"E{etype}D{edate}")
                if len(edate) > 4: keys.append(f"E{etype}Y{edate[0:4]}")
            if eplace: 
                eplace = sanitize(eplace)
                eplace = eplace.replace(" ","#")
                keys.append(f"E{etype}P{eplace}")
    searchkey1 = " ".join(sorted(keys))
    #print(searchkey1)
    run("match (p:Person) where id(p) = $pid set p.searchkey1=$searchkey1 return p",
        searchkey1=searchkey1,pid=pid)

def generate_searchkey(n,count,rec):   
    """
    generates searchkey for all persons
    """
    pid = rec.get('pid')
    p = rec.get('p')
    searchkey1 = p.get('searchkey1')
    parents = rec.get('parents')
    pkeys = []
    for n,parent in enumerate(parents):
        key = parent.get("searchkey1")
        if not key: 
            #raise RuntimeError(f"searchkey1 not found, person_id: {pid}, parent {parent}")
            continue # parent was probably added in another batch, ignore
        for k in key.split():
            #pkeys.append(f"Parent{n+1}{k}")
            pkeys.append(f"Parent{k}")
    psearchkey = " ".join(pkeys)
    searchkey = searchkey1 + " " + psearchkey
    
    run("""match (p:Person) where id(p) = $pid 
        set p.searchkey=$searchkey
        return p
        """,
        searchkey=searchkey,
        pid=pid)

def generate_keys(args):
    cypher1 = """
        match 
            (b:Batch)
        where $batch_id = '' or b.id = $batch_id
        match 
            (b:Batch)-->(p:Person)-[:NAME]->(pn:Name{order:0})
        optional match
            (rn:Refname)-[bn:BASENAME]->(p)
        optional match
            (e:Event)<-[:EVENT{role:'Primary'}]-(p)
        optional match
            (pl:Place)<--(e)
        return 
            id(p) as pid,
            pn,
            collect(distinct [rn,bn]) as refnames,
            collect(distinct [e,pl]) as events
    """
    if args.for_batch:
        batch_id = args.for_batch
    else:
        batch_id = ''

    run(cypher1, callback=generate_searchkey1, batch_id=args.for_batch)

    cypher2 = """
        match 
            (b:Batch)
        where $batch_id = '' or b.id = $batch_id
        match 
            (b)-->(p:Person)
        optional match
            (p)<-[:CHILD]-(fam:Family)-[:PARENT]->(parent:Person)
        return 
            id(p) as pid,
            p,
            collect(distinct parent) as parents
    """
    n = run(cypher2, callback=generate_searchkey, batch_id=args.for_batch)
    print(f"Generated searchkeys for {n} people")
    return n

def remove_keys(args):   
    cypher = """
        match 
            (b:Batch)
        where $batch_id = '' or b.id = $batch_id
        match (b) --> (p:Person)
        where exists(p.searchkey)  
        remove p.searchkey 
        remove p.searchkey1 
        return p
    """
    n = run(cypher,batch_id=args.from_batch)
    print(f"Removed searchkeys from {n} people")
    return n

def getname(namenode):
    firstname = namenode.get("firstname")
    patronyme = namenode.get("suffix")
    surname = namenode.get("surname")
    name = ''
    if firstname: 
        name = firstname
    if patronyme: 
        name += ' ' + patronyme
    if surname: 
        name += ' ' + surname
    return name.strip()

def display_matches(args,p,pid,pn,rec,matches):   
    score = rec.get('score')
    matchid = rec.get('node').get("id")
    matchname = rec.get('mn')
    matchnode = rec.get('node')
    matchpid = rec.get("matchpid")
    if score >= args.minscore:
        matchkeys = matchnode.get('searchkey')
        if len(matchkeys.split()) < args.minitems: return
        pdict1 = dict(p)
        pdict1['name'] = getname(pn)
        pdict1['pid'] = pid
        pdict2 = dict(matchnode)
        pdict2['name'] = getname(matchname)
        pdict2['pid'] = matchpid
        res = dict(score=score,p1=pdict1,p2=pdict2)
        matches.append(res)
    
def __search_dups(n,count,args,rec,matches):   
    pid = rec.get('pid')
    p = rec.get('p')
    pn = rec.get('pn')
    searchkey = p.get('searchkey')
    if searchkey is None: return
    keys = searchkey.split()
    if len(keys) < args.minitems: return 

    if args.namematch:
        name = getname(pn).lower()
        if name.find(args.namematch.lower()) < 0: return

    num_matches = run("""
        CALL db.index.fulltext.queryNodes("personIndex", $searchkey) YIELD node, score
        where id(node) <> $pid and score >= $minscore
        match 
            (b:Batch)
        where $batch_id = '' or b.id = $batch_id
        MATCH (b) --> (node) --> (mn:Name{order:0})
        RETURN node, score, mn, id(node) as matchpid   
    """,callback=lambda n,count,rec: display_matches(args,p,pid,pn,rec,matches),
        searchkey=searchkey,
        pid=pid,
        batch_id=args.batchid2,
        minscore=args.minscore,
        )
    #count = rec.get('count')
    print(f"Search: {n}/{count}: {num_matches} matches")
        
def search_dups(args):
    matches = []
    run("""
        match 
            (b:Batch)
        where $batch_id = '' or b.id = $batch_id
        match (b) --> (p:Person)--(pn:Name) 
        return id(p) as pid,p,pn
    """,callback=lambda n,count,rec: __search_dups(n,count,args,rec,matches), batch_id=args.batchid1)
    return sorted(matches,reverse=True,key=lambda match: match['score'])

def check_batch(batch_id):
    n = run("""
        match 
            (b:Batch)
        where $batch_id = '' or b.id = $batch_id
        return b
        """,    
        batch_id=batch_id)
    if n == 0:
        raise RuntimeError(f"No such batch: {batch_id}")


