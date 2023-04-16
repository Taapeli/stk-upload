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

import json
import time

from collections import defaultdict
from difflib import HtmlDiff as _mdiff
from types import SimpleNamespace

from flask import render_template, request, jsonify, flash #, session as user_session
from flask_security import login_required, roles_required
#from flask_security import current_user
from flask_babelex import _
from . import bp

from bl.batch.root import Root, State
from bp.dupsearch.models import search
from ui.context import UserContext
from bl.person_reader import PersonReaderTx
from bl.base import Status
from dns.rdataclass import NONE
#from bl.material import Material


@bp.route('/dupsearch',  methods=['GET'])
@login_required
@roles_required('audit')
def dupsearch():
    return render_template('/dupsearch.html')

@bp.route('/dupsearch/batches1',  methods=['GET'])
@login_required
@roles_required('audit')
def batches1():
    batch_list = list(Root.get_batches())
    completed_batches = []
    for b in batch_list:
        file = b.get('file')
        status = b.get('state')
        if file and status == State.ROOT_CANDIDATE:
            file = file.split("/")[-1].replace("_clean.gramps",".gramps")
            file = file.split("/")[-1].replace("_clean.gpkg",".gpkg")
            b['file'] = file 
            completed_batches.append(b)
    return jsonify(completed_batches)

@bp.route('/dupsearch/batches',  methods=['GET'])
@login_required
@roles_required('audit')
def batches():
    batch_list = search.batches()
    completed_batches = []
    for b in batch_list:
        #print(b)
        file = b.get('file')
        _status = b.get('state')
        if file: # and _status == State.ROOT_CANDIDATE:
            file = file.split("/")[-1].replace("_clean.gramps",".gramps")
            file = file.split("/")[-1].replace("_clean.gpkg",".gpkg")
            b['file'] = file 
            completed_batches.append(b)
    return jsonify(completed_batches)

@bp.route('/dupsearch/generate_keys/<batchid>/<namematch_algo>',  methods=['GET'])
@login_required
@roles_required('audit')
def generate_keys(batchid,namematch_algo):
    args = SimpleNamespace(for_batch=batchid, namematch_algo=namematch_algo)
    res = search.generate_keys(args)
    return jsonify(res)

@bp.route('/dupsearch/remove_keys/<batchid>',  methods=['GET'])
@login_required
@roles_required('audit')
def remove_keys(batchid):
    args = SimpleNamespace(from_batch=batchid)
    res = search.remove_keys(args)
    return jsonify(res)

@bp.route('/dupsearch/search', methods=['POST'])
@login_required
@roles_required('audit')
def search_dups():
    args_dict = json.loads(request.data)
    args = SimpleNamespace(**args_dict)
    args.minscore = float(args.minscore)
    args.minitems = int(args.minitems)
    t1 = time.time()
    res = search.search_dups(args)
    t2 = time.time()
    print(f"Elapsed: {t2-t1}s")
    return jsonify(res)

@bp.route('/dupsearch/create_index/<batch_id>', methods=['GET'])
@login_required
@roles_required('audit')
def create_index(batch_id):
    res = search.create_index(batch_id)
    return jsonify(res)

@bp.route('/dupsearch/drop_index/<batch_id>', methods=['GET'])
@login_required
@roles_required('audit')
def drop_index(batch_id):
    res = search.drop_index(batch_id)
    return jsonify(res)

@bp.route('/dupsearch/get_models', methods=['GET'])
@login_required
@roles_required('audit')
def get_models():
    res = search.get_models()
    return jsonify(res)

@bp.route('/dupsearch/upload', methods=['POST'])
@roles_required('audit')
@login_required
def upload():
    file = request.files['file']
    res = search.upload(file)
    return jsonify(res)

def _get_person(service, iid):
    result = service.get_person_data(iid)

    # result {'person':PersonBl, 'objs':{uniq_id:obj}, 'jscode':str, 'root':{root_type,root_user,batch_id}}
    if Status.has_failed(result):
        flash(f'{result.get("statustext","error")} – {iid}', "error")
        return None, []
    else:
        person = result.get("person")
        objs = result.get("objs", [])
        person.root = result.get("root")
        return person, objs


@bp.route('/dupsearch/compare', methods=['GET'])
@login_required
@roles_required('audit')
def compare():
    """ Compare by something? """
    material_type = "Family Tree"
    iid1 = request.args.get("iid1")
    u_context1 = UserContext()
    u_context1.material.batch_id =  request.args.get("batch_id1")
    u_context1.material.m_type = material_type
    u_context1.state = request.args.get("state1")
    if u_context1.state == State.ROOT_ACCEPTED: # "Accepted":        
        u_context1.user = None

    iid2 = request.args.get("iid2")
    u_context2 = UserContext()
    u_context2.material.batch_id =  request.args.get("batch_id2")
    u_context2.material.m_type = material_type
    u_context2.state = request.args.get("state2")
    if u_context2.state == State.ROOT_ACCEPTED: #"Accepted":        
        u_context2.user = None

    with PersonReaderTx("read_tx", u_context1) as service:
        person1,objs1 = _get_person(service, iid1)

    with PersonReaderTx("read_tx", u_context2) as service:
        person2,objs2 = _get_person(service, iid2)

#     return render_template('/compare.html',
#                            batch_id1=batch_id1, 
#                            person1=person1,
#                            objs1=objs1,
#                            batch_id2=batch_id2, 
#                            person2=person2,
#                            objs2=objs2)

    SEP = "###"
    def person_name(p):
        n = p.names[0]
        return f"{n.firstname} {n.suffix} {n.surname}" 
    
    def person_names(p):
        for n in p.names:
            yield f"{n.firstname} {n.suffix} {n.surname}" 

    def events1(p,lines, objs):
        for e in p.events:
            places = [objs[ref].names[0].name for ref in e.place_ref]
            place = "/".join(places)
            lines.append(f"{e.type}{SEP}{e.dates}{SEP}{place}{SEP}{e.description}")
        
    def events(p,lines, objs,eventtypes, mod=False):
        for e in p.events:
            places = [objs[ref].names[0].name for ref in e.place_ref]
            place = "/".join(places)
            #if mod: place = place.replace("a","x")
            eventtypes[_(e.type).lower()].append(f"{e.dates}{SEP}{place}{SEP}{e.description}")

    def eventsort(etype):
        if etype == _("Birth"): return (0,etype)
        if etype == _("Baptism"): return (1,etype)
        if etype == _("Death"): return (3,etype)
        if etype == _("Burial"): return (4,etype)
        # all others:
        return (2,etype)

    def fixline(line):
        line = line.strip()
        print("line:",line)
        KEYS = ['\0+','\0-','\0^']
        for key in KEYS:
            i = 0
            while True:
                i = line.find(key, i)
                if i < 0:
                    break
                j = line.find('\1',i)
                span = line[i+2:j]
                span2 = span.replace(SEP,'\1'+SEP+key)
                line = line[0:i+2] + span2 + line[j:]
                i = i+2+len(span2)
        print("line2:",line)
        return line
    
    return render_template('/compare.html',
                           batch_id1=u_context1.material.batch_id, 
                           person1=person1,
                           objs1=objs1,
                           batch_id2=u_context2.material.batch_id, 
                           person2=person2,
                           objs2=objs2)

@bp.route('/dupsearch/compare2', methods=['GET'])
@login_required
@roles_required('audit')
def compare2():
    """ Compare by names. """
    iid1 = request.args.get("iid1")
    u_context1 = UserContext()
    u_context1.material.batch_id =  request.args.get("batch_id1")
    u_context1.state = request.args.get("state1")
    if u_context1.state == State.ROOT_ACCEPTED: # "Accepted":        
        u_context1.user = None

    iid2 = request.args.get("iid2")
    u_context2 = UserContext()
    u_context2.material.batch_id =  request.args.get("batch_id2")
    u_context2.state = request.args.get("state2")
    if u_context2.state == State.ROOT_ACCEPTED: #"Accepted":        
        u_context2.user = None
    
    with PersonReaderTx("read_tx", u_context1) as service:
        person1,objs1 = _get_person(service, iid1)

    with PersonReaderTx("read_tx", u_context2) as service:
        person2,objs2 = _get_person(service, iid2)
    
#     return render_template('/compare.html',
#                            batch_id1=batch_id1, 
#                            person1=person1,
#                            objs1=objs1,
#                            batch_id2=batch_id2, 
#                            person2=person2,
#                            objs2=objs2)

    SEP = "###"
    def person_name(p):
        n = p.names[0]
        return f"{n.firstname} {n.suffix} {n.surname}" 
    
    def person_names(p):
        for n in p.names:
            yield f"{n.firstname} {n.suffix} {n.surname}" 

    def events1(p,lines, objs):
        for e in p.events:
            places = [objs[ref].names[0].name for ref in e.place_ref]
            place = "/".join(places)
            lines.append(f"{e.type}{SEP}{e.dates}{SEP}{place}{SEP}{e.description}")
        
    def events(p,lines, objs,eventtypes, mod=False):
        for e in p.events:
            places = [objs[ref].names[0].name for ref in e.place_ref]
            place = "/".join(places)
            #if mod: place = place.replace("a","x")
            eventtypes[_(e.type).lower()].append(f"{e.dates}{SEP}{place}{SEP}{e.description}")

    def eventsort(etype):
        if etype == _("Birth"): return (0,etype)
        if etype == _("Baptism"): return (1,etype)
        if etype == _("Death"): return (3,etype)
        if etype == _("Burial"): return (4,etype)
        # all others:
        return (2,etype)

    def fixline(line):
        line = line.strip()
        print("line:",line)
        KEYS = ['\0+','\0-','\0^']
        for key in KEYS:
            i = 0
            while True:
                i = line.find(key, i)
                if i < 0:
                    break
                j = line.find('\1',i)
                span = line[i+2:j]
                span2 = span.replace(SEP,'\1'+SEP+key)
                line = line[0:i+2] + span2 + line[j:]
                i = i+2+len(span2)
        print("line2:",line)
        return line
    
    # name1 = person_name(person1)
    # name2 = person_name(person2)
    lines1 = []
    lines2 = []
    
    #lines1.append("Names")
    #lines1.append(name1)
    #lines1.append(name1)
    for name in person_names(person1):
        lines1.append(name)
    for name in person_names(person2):
        lines2.append(name)

    #lines2.append("Names")
    #lines2.append(name2)
    # namelines = HtmlDiff().make_table(lines1,lines2,context=False)
    namelines = ""
    for (_linenum1,line1),(_linenum2,line2),_flag in _mdiff(lines1,lines2):
        if line1 == '\n': line1 = ""  # placeholders for the missing columns
        line = f"<tr><td><td colspan=3>" + fixline(line1) + "</td>\n<td colspan=3>" + fixline(line2) + "</td></tr>\n"
        namelines += line
    namelines = namelines.replace('\0+','<span class="diff_add">'). \
                 replace('\0-','<span class="diff_sub">'). \
                 replace('\0^','<span class="diff_chg">'). \
                 replace('\1','</span>'). \
                 replace('\t','&nbsp;'). \
                 replace(SEP,"<td>")
    print(namelines)
    eventtypes1 = defaultdict(list)
    eventtypes2 = defaultdict(list)
    events(person1,lines1, objs1, eventtypes1)
    events(person2,lines2, objs2, eventtypes2, 1)
    table = ""
    eventtypes = sorted(set(eventtypes1).union(set(eventtypes2)), key=eventsort)
    for etype in eventtypes:
        lines1 = []
        lines2 = []
        lines1.extend(eventtypes1[etype])
        lines2.extend(eventtypes2[etype])
        for (_linenum1,line1),(_linenum2,line2),_flag in _mdiff(lines1,lines2):
            if line1 == '\n': line1 = "<td><td>"  # placeholders for the missing columns
            line = f"<tr><td class=ColumnEvent>{etype}<td class=ColumnDate>" + fixline(line1) + "</td>\n<td class=ColumnDate>" + fixline(line2) + "</td></tr>\n"
            table += line
    difftable = table.replace('\0+','<span class="diff_add">'). \
                 replace('\0-','<span class="diff_sub">'). \
                 replace('\0^','<span class="diff_chg">'). \
                 replace('\1','</span>'). \
                 replace('\t','&nbsp;'). \
                 replace(SEP,"<td>")

    return render_template('/compare2.html',
                           namelines=namelines,
                           difftable=difftable,
                           batch_id1=u_context1.material.batch_id, 
                           person1=person1,
                           objs1=objs1,
                           batch_id2=u_context2.material.batch_id, 
                           person2=person2,
                           objs2=objs2)
