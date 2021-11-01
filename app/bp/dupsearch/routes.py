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
from types import SimpleNamespace

from flask import render_template, request, jsonify, flash,  session as user_session
from flask_security import login_required, roles_required
from flask_security import current_user
#from flask_babelex import _
from . import bp

from bl.root import Root, State
from bp.dupsearch.models import search
from ui.user_context import UserContext
from bl.person_reader import PersonReaderTx
from bl.base import Status

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
        status = b.get('state')
        if file: # and status == State.ROOT_CANDIDATE:
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


@bp.route('/dupsearch/compare', methods=['GET'])
@login_required
@roles_required('audit')
def compare():
    uuid1 = request.args.get("uuid1")
    uuid2 = request.args.get("uuid2")
    batch_id1 = request.args.get("batch_id1")
    batch_id2 = request.args.get("batch_id2")
    state1 = request.args.get("state1")
    state2 = request.args.get("state2")
    
    def get_person(service, uuid):
        result = service.get_person_data(uuid)

        # result {'person':PersonBl, 'objs':{uniq_id:obj}, 'jscode':str, 'root':{root_type,root_user,batch_id}}
        if Status.has_failed(result):
            flash(f'{result.get("statustext","error")}', "error")
            person = None
            objs = []
        else:
            person = result.get("person")
            objs = result.get("objs", [])
            person.root = result.get("root")
            return person, objs
        
    u_context1 = UserContext(user_session, current_user, request)
    u_context2 = UserContext(user_session, current_user, request)
    if state1 == "Accepted":        
        u_context1.user = None
        
    if state2 == "Accepted":        
        u_context2.user = None

    u_context1.batch_id = batch_id1
    with PersonReaderTx("read_tx", u_context1) as service:
        person1,objs1 = get_person(service, uuid1)

    u_context2.batch_id = batch_id2
    with PersonReaderTx("read_tx", u_context2) as service:
        person2,objs2 = get_person(service, uuid2)
    
    return render_template('/compare.html', 
                           person1=person1,
                           objs1=objs1,
                           person2=person2,
                           objs2=objs2)
