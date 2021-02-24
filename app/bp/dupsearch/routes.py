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

from flask import render_template, request, jsonify #, redirect, url_for, session
from flask_security import login_required, roles_required
#from flask_babelex import _
from . import bp

#from bp.gramps.models import batch
from bl.batch import Batch
from bp.dupsearch.models import search
from types import SimpleNamespace
import json


@bp.route('/dupsearch',  methods=['GET'])
@login_required
@roles_required('audit')
def dupsearch():
    return render_template('/dupsearch.html')

@bp.route('/dupsearch/batches',  methods=['GET'])
@login_required
@roles_required('audit')
def batches():
    batch_list = list(Batch.get_batches())
    completed_batches = []
    for b in batch_list:
        file = b.get('file')
        status = b.get('status')
        if file and status == 'completed':
            file = file.split("/")[-1].replace("_clean.gramps",".gramps")
            b['file'] = file 
            completed_batches.append(b)
    return jsonify(completed_batches)

@bp.route('/dupsearch/generate_keys/<batchid>',  methods=['GET'])
@login_required
@roles_required('audit')
def generate_keys(batchid):
    args = SimpleNamespace(for_batch=batchid)
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
    res = search.search_dups(args)
    return jsonify(res)

@bp.route('/dupsearch/create_index', methods=['GET'])
@login_required
@roles_required('audit')
def create_index():
    res = search.create_index(None)
    return jsonify(res)

@bp.route('/dupsearch/drop_index', methods=['GET'])
@login_required
@roles_required('audit')
def drop_index():
    res = search.drop_index(None)
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

