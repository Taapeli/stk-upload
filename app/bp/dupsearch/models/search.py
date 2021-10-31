#   Isotammi Genealogical Service for combining multiple researchers' results.
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

from bl.event import Event
from bl.refname import Refname
import shareds

from neo4j import GraphDatabase
from werkzeug.utils import secure_filename
import subprocess
from operator import itemgetter
import functools
import time
from pprint import pprint

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
    #print("run",cypher)
    try:
        res = neo4j_driver.session().run(cypher, kwargs)
        n = 0
        reslist = list(res)
        count = len(reslist)
        #print("-count:",count)
        for rec in reslist:
            n += 1
            if callback: callback(n,count,rec, kwargs)
        return n
    except:
        traceback.print_exc()
        raise

def read_hiskidata():
    hiskinames = {}
    fname = os.path.join(os.path.dirname(__file__),"refnames.txt")
    for line in open(fname):
        #print(line) 
        if line.strip() == "": continue
        _, name, refname = line.split()
        hiskinames[name] = refname
    return hiskinames
        
#hiskinames = read_hiskidata()

def index_name_from_batch_id(batch_id):
    return "searchkey_" + batch_id.replace("-","_").replace(".","_")

def create_index(batch_id):
    index_name = index_name_from_batch_id(batch_id)
    run(f"""
        CALL db.index.fulltext.createNodeIndex(
        "{index_name}",["Person"],["{index_name}"])
    """)   

def drop_index(batch_id):
    index_name = index_name_from_batch_id(batch_id)
    run(f"CALL db.index.fulltext.drop('{index_name}')") 

def list_indexes(args):
    run("CALL db.indexes",callback=print)

def list_batches(args):
    id = 'id'
    user = 'user'
    file = 'file'
    status = 'status'
    #print(f"{id:14s} {user:16s} {file:60s} {status}")
    run("match (b:Root) return b",callback=list_batch)

def batches():
    cypher = """
        match (b:Root) return b
    """
    batchlist = []
    run(cypher,callback=lambda n,count,rec, kwargs: batchlist.append(dict(rec.get('b'))))
    return batchlist

def list_batch(rec):
    batch = rec.get('b')
    file = batch.get('file')
    id = batch.get('id')
    user = batch.get('user')
    status = batch.get('state')
    print(f"{id:14s} {user:16s} {file:60s} {status}")

def normalize_name(name_normalizer,name,nametype):
    name1 = name
    name = re.sub(r"[^a-z|0-9|åöä]","_",name,flags=re.IGNORECASE)
    if name_normalizer:
        name = name_normalizer((nametype,name),name)
    #print("name_normalizer",name1,"->",name)
    return name

def generate_searchkey1(name_normalizer, n,count,rec, kwargs):   
    """
    generates searchkey1 for all persons
    """
    if n % 100 == 0: print(f"Phase 1: {n}/{count}")
    keys = []
    pid = rec.get('pid')
    refnames = rec.get('refnames')
    #print("refnames:", refnames)
    for (rn,bn) in refnames:
        #print(rn,bn)
        if rn is None or bn is None: continue
        if bn.get('use') == 'firstname': 
            fname = rn.get('name')
            if fname: 
                fname = normalize_name(name_normalizer,fname,'firstname')
                for n in fname.split(): keys.append("G"+n)
        if bn.get('use') == 'surname': 
            sname = rn.get('name')
            if sname: 
                sname = normalize_name(name_normalizer,sname,'surname')
                for n in sname.split(): keys.append("L"+n)
        if bn.get('use') == 'patronyme': 
            patronyme = rn.get('name')
            if patronyme: 
                patronyme = normalize_name(name_normalizer,patronyme,'patronyme')
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
                eplace = normalize_name(name_normalizer,eplace,'pname')
                eplace = eplace.replace(" ","#")
                keys.append(f"E{etype}P{eplace}")
    searchkey1 = " ".join(sorted(keys))
    
    #print(searchkey1)
    run("match (p:Person) where id(p) = $pid set p.searchkey1=$searchkey1 return p",
        searchkey1=searchkey1,pid=pid)

def generate_searchkey(n,count,rec, kwargs):   
    """
    generates searchkey for all persons
    """
    if n % 100 == 0: print(f"Phase 2: {n}/{count}")
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
    
    batch_id = kwargs['batch_id']
    index_name = index_name_from_batch_id(batch_id)
    run(f"""match (p:Person) where id(p) = $pid 
        set p.{index_name}=$searchkey
        return p
        """,
        searchkey=searchkey,
        pid=pid)

def generate_keys(args):
    cypher1 = """
        match 
            (b:Root{id:$batch_id})
        match 
            (b)-->(p:Person)-[:NAME]->(pn:Name{order:0})
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

    refnames = get_refnames() # mapping of (nametype,name) -> refname
    name_normalizer = refnames.get
    run(cypher1, callback=functools.partial(generate_searchkey1, name_normalizer), 
        batch_id=args.for_batch)

    cypher2 = """
        match 
            (b:Root)
        where $batch_id = '' or b.id = $batch_id
        match 
            (b)-->(p:Person)
        optional match
            (p)<-[:CHILD]-(fam:Family)-[:PARENT]->(parent:Person),
            (b) --> (fam)
        set b.has_searchkeys = true,
            b.namematch_algo = $namematch_algo
        return 
            id(p) as pid,
            p,
            collect(distinct parent) as parents
    """
    n = run(cypher2, callback=generate_searchkey, batch_id=args.for_batch, namematch_algo=args.namematch_algo)
    create_index(args.for_batch)
    print(f"Generated searchkeys and index for {n} people")
    return n

def remove_keys(args):   
    index_name = index_name_from_batch_id(args.from_batch)
    cypher = f"""
        match (b:Root{{id:$batch_id}}) --> (p:Person)
        remove p.searchkey 
        remove p.searchkey1 
        remove p.{index_name} 
        remove b.has_searchkeys
        return p
    """
    n = run(cypher,batch_id=args.from_batch)
    drop_index(args.from_batch)
    print(f"Removed searchkeys and index from {n} people")
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
        'EBirthD','EBirthY','EBirthP',
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
        
def display_matches(args,p,pid,pn,rec,matches,index_name1,index_name2):   
#     print("        display_matches",p) 
#     print("        display_matches",rec) 
    score = rec.get('score')
    matchid = rec.get('node').get("id")
    namenodes = rec.get('namenodes') # there may be several Name nodes with order:0, pick the first
    matchname = namenodes[0]
    matchnode = rec.get('node')
    matchpid = rec.get("matchpid")
    #print(p['searchkey']) 
    #print(matchnode['searchkey'])
    
    if 1 or score >= args.minscore:
        matchkeys = matchnode.get(index_name2)
        if len(matchkeys.split()) < args.minitems: return
        pdict1 = dict(p)
        pdict1['name'] = getname(pn)
        pdict1['pid'] = pid
        pdict1['searchkey'] = p.get(index_name1)
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
#     print()
#     print("__search_dups",n,count,rec)
    index_name = index_name_from_batch_id(args.batchid1)
    index_name2 = index_name_from_batch_id(args.batchid2)
    if n % 100 == 0: print(f"{time.time()-t0}: Searching {n}/{count}")
    pid = rec.get('pid')
    p = rec.get('p')
    gid = p.get('id')
    print("gid2",gid)
    gids.add(gid)

    namenodes = rec.get('namenodes') # there may be several Name nodes with order:0, pick the first
    pn = namenodes[0]

    searchkey = p.get(index_name)
    if searchkey is None: 
        print("searchkey not found")
        return
    keys = searchkey.split()
    if len(keys) < args.minitems: return 

    if args.namematch:
        name = getname(pn).lower()
        if name.find(args.namematch.lower()) < 0: return

    num_matches = run(f"""
        CALL db.index.fulltext.queryNodes("{index_name2}", $searchkey) YIELD node, score
        where id(node) <> $pid 
        match (node) --> (mn:Name{{order:0}})
        RETURN node, score, collect(mn) as namenodes, id(node) as matchpid   
        order by score desc
        limit 50
    """,callback=lambda n,count,rec,kwargs: display_matches(args,p,pid,pn,rec,matches,index_name,index_name2),
        searchkey=searchkey,
        pid=pid,
        batch_id=args.batchid2,
        minscore=args.minscore,
        )
    return 
    
gids = set()
def search_dups(args):
    print(args)
    print(args.model)
    global t0
    t0 = time.time()
    matches = []
    run("""
        match (b:Root{id:$batch_id}) -[:OBJ_PERSON]-> (p:Person) -[:NAME]-> (pn:Name{order:0}) 
        return id(p) as pid, p, collect(pn) as namenodes
    """,callback=lambda n,count,rec,kwargs: __search_dups(n,count,args,rec,matches), 
        batch_id=args.batchid1)

    print("num matches:", len(matches))
    matches = prune_matches(matches)
    print("pruned matches:", len(matches))
    for m in matches:
        p1 = m['p1']
        gid = p1.get("id")
        if gid in gids: gids.remove(gid)
    print("gids:", gids)
    return sorted(matches,reverse=True,key=itemgetter('score')) #[0:50]


def get_refnames_by_type(nametype):
    refnames = Refname.get_refnames() 
    namemap = {}
    for refname in refnames:
        if refname.reftype.find(nametype) < 0: continue
        if refname.refname:
            namemap[refname.name] = refname.refname
        else:
            namemap[refname.name] = refname.name
    return namemap

def get_refnames():
    refnames = Refname.get_refnames() 
    namemap = {}
    for refname in refnames:
        #if refname.reftype.find(nametype) < 0: continue
        for nametype in refname.reftype.split():
            if refname.refname:
                namemap[(nametype,refname.name)] = refname.refname
            else:
                namemap[(nametype,refname.name)] = refname.name
    return namemap

def prune_matches(matches):
    refnames = get_refnames_by_type("firstname") # mapping of name -> refname
    #pprint(refnames['Aina'])
    def get_firstnames(key):
        words = key.split()
        #print(words)
        names = [refnames.get(value[1:],value[1:]) for value in words if value[0] == "G"]
        return set(names)
    
    #====== Duplicate!? =======================================================
    # def get_firstnames(key):
    #     words = key.split()
    #     names = [value[1:] for value in words if value[0] == "G"]
    #     return set(names)
    #==========================================================================

     
    matches2 = []
    for match in matches:
        p1 = match['p1']
        p2 = match['p2']

        gender1 = p1['sex']
        gender2 = p2['sex']
        if gender1 > 0 and gender2 > 0 and gender1 != gender2: continue

        birth_low1 = p1['birth_low']
        birth_low2 = p2['birth_low']
        birth_high1 = p1['birth_high']
        birth_high2 = p2['birth_high']

        death_low1 = p1['death_low']
        death_low2 = p2['death_low']
        death_high1 = p1['death_high']
        death_high2 = p2['death_high']
        if birth_high1 < birth_low2: continue
        if birth_high2 < birth_low1: continue
        if death_high1 < death_low2: continue
        if death_high2 < death_low1: continue

        key1 = p1['searchkey']
        key2 = p2['searchkey']
        firstnames1 = get_firstnames(key1)
        firstnames2 = get_firstnames(key2)
#         firstnames1 = get_firstnames(key1, refnames)
#         firstnames2 = get_firstnames(key2, refnames)
#         firstnames1 = set(key1.split())
#         firstnames2 = set(key2.split())

#         common_names = firstnames1 & firstnames2
#         if len(common_names) == 0: continue
#         if common_names != firstnames1 and common_names != firstnames2: continue
        
        matches2.append(match)
    return matches2

def check_batch(batch_id):
    n = run("""
        match 
            (b:Root)
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


