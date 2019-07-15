from flask import render_template, request, redirect, url_for, session, jsonify
from flask_security import login_required, roles_accepted, roles_required, current_user
from flask_babelex import _
from . import bp

from bp.gramps.models import batch
from bp.dupsearch.models import search
from types import SimpleNamespace
import json

@bp.route('/dupsearch',  methods=['GET'])
@login_required
def dupsearch():
    return render_template('/dupsearch.html')

@bp.route('/dupsearch/batches',  methods=['GET'])
@login_required
def batches():
    batch_list = list(batch.get_batches())
    for b in batch_list:
        file = b.get('file')
        if file:
            file = file.split("/")[-1].replace("_clean.",".")
            b['file'] = file 
    return jsonify(batch_list)

@bp.route('/dupsearch/generate_keys/<batchid>',  methods=['GET'])
@login_required
def generate_keys(batchid):
    args = SimpleNamespace(for_batch=batchid)
    res = search.generate_keys(args)
    return jsonify(res)

@bp.route('/dupsearch/remove_keys/<batchid>',  methods=['GET'])
@login_required
def remove_keys(batchid):
    args = SimpleNamespace(from_batch=batchid)
    res = search.remove_keys(args)
    return jsonify(res)

@bp.route('/dupsearch/search', methods=['POST'])
@login_required
def search_dups():
    args_dict = json.loads(request.data)
    args = SimpleNamespace(**args_dict)
    args.minscore = float(args.minscore)
    args.minitems = int(args.minitems)
    res = search.search_dups(args)
    return jsonify(res)

@bp.route('/dupsearch/create_index', methods=['GET'])
@login_required
def create_index():
    res = search.create_index(None)
    return jsonify(res)

@bp.route('/dupsearch/drop_index', methods=['GET'])
@login_required
def drop_index():
    res = search.drop_index(None)
    return jsonify(res)
