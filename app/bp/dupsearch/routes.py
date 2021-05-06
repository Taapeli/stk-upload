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

from flask import render_template, request, jsonify #, redirect, url_for, session
from flask_security import login_required, roles_required
#from flask_babelex import _
from . import bp

#from bp.gramps.models import batch
from bl.batch import Batch
from bp.dupsearch.models import search

@bp.route('/dupsearch',  methods=['GET'])
@login_required
@roles_required('audit')
def dupsearch():
    return render_template('/dupsearch.html')

@bp.route('/dupsearch/batches1',  methods=['GET'])
@login_required
@roles_required('audit')
def batches1():
    batch_list = list(Batch.get_batches())
    completed_batches = []
    for b in batch_list:
        file = b.get('file')
        status = b.get('status')
        if file and status == 'completed':
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
        status = b.get('status')
        if file and status == 'completed':
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
@login_required
@roles_required('audit')
def upload():
    file = request.files['file']
    res = search.upload(file)
    return jsonify(res)

