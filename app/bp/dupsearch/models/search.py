#   Isotammi Geneological Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

#!/usr/bin/env python
import os
import re
import traceback

from neo4j import GraphDatabase
from models.gen.event import Event
import shareds

from werkzeug.utils import secure_filename
import subprocess

# https://neo4j.com/developer/kb/fulltext-search-in-neo4j/
# https://neo4j.com/docs/cypher-manual/3.5/schema/index/#schema-index-fulltext-search
# http://lucene.apache.org/core/5_5_0/queryparser/org/apache/lucene/queryparser/classic/package-summary.html#package.description
#
# Requires Neo4j 3.5 or later

neo4j_uri = shareds.app.config.get("NEO4J_URI")
neo4j_username = shareds.app.config.get("NEO4J_USERNAME")
neo4j_password = shareds.app.config.get("NEO4J_PASSWORD")
libsvm_folder = shareds.app.config.get("LIBSVM_FOLDER")

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
    return re.sub(r"[^a-z|0-9|åöä]","_",name,flags=re.IGNORECASE)
    
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
        edate = event.dates.estimate()
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
    pkeys = set()
    for n,parent in enumerate(parents):
        key = parent.get("searchkey1")
        if not key: 
            #raise RuntimeError(f"searchkey1 not found, person_id: {pid}, parent {parent}")
            continue # parent was probably added in another batch, ignore
        for k in key.split():
            #pkeys.append(f"Parent{n+1}{k}")
            pkeys.add(f"Parent{k}")
    psearchkey = " ".join(sorted(pkeys))
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
            (rn:Refname)-[bn:REFNAME]->(p)
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
            (p)<-[:CHILD]-(fam:Family)-[:PARENT]->(parent:Person),
            (b) --> (fam)
        set b.has_searchkeys = true
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
        remove b.has_searchkeys
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


def getvalue(searchkeys, prefix):
    valueset = set()
    for key in searchkeys:
        if key.startswith(prefix): valueset.add( key[len(prefix):] )
    if len(valueset) == 0:
        return None
    else:
        return valueset

def compute_match(searchkey1,searchkey2):
    keys1 = searchkey1.split()
    keys2 = searchkey2.split()
    matchvalues = []
    for prefix in (
        'G','L','X',
        'EBirthD','EBirthY','EBirthP    '
        'EDeathD','EDeathY','EDeathP',
    ):
        value1 = getvalue(keys1,prefix)
        value2 = getvalue(keys2,prefix)
        value = 1 if value1 and value2 and value1 == value2 else 0
        matchvalues.append(value)

        value1 = getvalue(keys1,"Parent"+prefix)
        value2 = getvalue(keys2,"Parent"+prefix)
        value = 1 if value1 and value2 and value1 == value2 else 0
        matchvalues.append(value)
    return tuple(matchvalues)
        
def display_matches(args,p,pid,pn,rec,matches):   
    score = rec.get('score')
    matchid = rec.get('node').get("id")
    namenodes = rec.get('namenodes') # there may be several Name nodes with order:0, pick the first
    matchname = namenodes[0]
    matchnode = rec.get('node')
    matchpid = rec.get("matchpid")
    if score >= args.minscore:
        matchkeys = matchnode.get('searchkey')
        if len(matchkeys.split()) < args.minitems: return
        pdict1 = dict(p)
        pdict1['name'] = getname(pn)
        pdict1['pid'] = pid
        pdict1['searchkey'] = p.get('searchkey')
        pdict2 = dict(matchnode)
        pdict2['name'] = getname(matchname)
        pdict2['pid'] = matchpid
        pdict2['searchkey'] = matchkeys
        matchvector = compute_match(pdict1['searchkey'],pdict2['searchkey'])
        #score = score * sum(matchvector)
        matchvectorstring = "".join([str(x) for x in matchvector])
        res = dict(score=score,matchvector=matchvectorstring,p1=pdict1,p2=pdict2)
        matches.append(res)
        
    
def __search_dups(n,count,args,rec,matches):   
    if n % 100 == 0: print(f"Searching {n}/{count}")
    pid = rec.get('pid')
    p = rec.get('p')

    namenodes = rec.get('namenodes') # there may be several Name nodes with order:0, pick the first
    pn = namenodes[0]

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
        MATCH (b:Batch{id:$batch_id}) --> (node) --> (mn:Name{order:0})
        RETURN node, score, collect(mn) as namenodes, id(node) as matchpid   
    """,callback=lambda n,count,rec: display_matches(args,p,pid,pn,rec,matches),
        searchkey=searchkey,
        pid=pid,
        batch_id=args.batchid2,
        minscore=args.minscore,
        )

    
def search_dups(args):
    print(args)
    print(args.model)
    matches = []
    run("""
        match (b:Batch{id:$batch_id}) -[:OWNS]-> (p:Person) -[:NAME]-> (pn:Name{order:0}) 
        return id(p) as pid, p, collect(pn) as namenodes
    """,callback=lambda n,count,rec: __search_dups(n,count,args,rec,matches), batch_id=args.batchid1)

    test_data = "kku/test_data.txt"
    with open(test_data,"w") as f:
        value = 0
        for res in matches:
            values = " ".join(["%s:%s" % (i+1,value) for (i,value) in enumerate(res['matchvector'])])
            matchdata = "{} {}\n".format(value,values)
            f.write(matchdata)
            value = 1-value
    from subprocess import Popen, PIPE
    models_folder = "training/models"
    model = os.path.join(models_folder,args.model)
    output_file = "/tmp/output.txt"
    cmd = f"{libsvm_folder}/svm-predict {test_data} {model} {output_file}"
    f = subprocess.run(cmd, shell = True ) #, stdout = PIPE).stdout
    for i,line in enumerate(open(output_file)):
        matches[i]['match_value'] = int(line)

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


def upload(file):
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '': # pragma: no cover
        return dict(status='error')
    print(file.filename)
    filename = secure_filename(file.filename)
    training_data_folder = "training/data"
    models_folder = "training/models"
    os.makedirs(training_data_folder, exist_ok=True)
    os.makedirs(models_folder, exist_ok=True)
    fullname = os.path.join(training_data_folder, filename)
    file.save(fullname)

    model = os.path.join(models_folder, filename)
    cmd = f"{libsvm_folder}/svm-train {fullname} {model}"
    f = subprocess.run(cmd, shell = True ) 
    return dict(status='ok')


def get_models():
    models_folder = "training/models"
    os.makedirs(models_folder, exist_ok=True)
    return os.listdir(models_folder)


