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
#
#   Two-way fanchart adapted from Vasco Asturiano's sunburst chart javascript module
#   (https://github.com/vasturiano/sunburst-chart).
#
#   Copyright (C) 2021  Heikki Roikonen

from flask import render_template, request, json
from flask_security import login_required, roles_accepted, current_user
from . import bp
from bp.graph.models.fanchart import FanChart
from bp.graph.models.famtree import FamTree

@bp.route('/fanchart', methods=['GET'])
@login_required
@roles_accepted('audit')
def fanchart_only(uuid=None):
    uuid = request.args.get('uuid', None)
    if uuid is None:
        return render_template('/graph/layout.html', fanchart_data='')

    fanchart = FanChart().get(uuid)
    return render_template('/graph/layout.html', fanchart_data=json.dumps(fanchart))

@bp.route('/famtree', methods=['GET'])
@login_required
@roles_accepted('audit')
def famtree_only(uuid=None):
    uuid = request.args.get('uuid', None)
    if uuid is None:
        return render_template('/graph/famtree.html', famtree_data='')

    famtree = FamTree().get(uuid)
    return render_template('/graph/famtree.html', famtree_data=json.dumps(famtree))

@bp.route('/force', methods=['GET'])
@login_required
@roles_accepted('audit')
def force_only(uuid=None):
    uuid = request.args.get('uuid', None)
    if uuid is None:
        return render_template('/graph/force.html', famtree_data='')

    famtree = FamTree().get(uuid)
    return render_template('/graph/force.html', famtree_data=json.dumps(famtree))

@bp.route('/tree', methods=['GET'])
@login_required
@roles_accepted('audit')
def tree_only(uuid=None):
    uuid = request.args.get('uuid', None)
    if uuid is None:
        return render_template('/graph/tree.html', famtree_data='')

    famtree = FamTree().get(uuid)
    return render_template('/graph/tree.html', famtree_data=json.dumps(famtree))

@bp.route('/yeartree', methods=['GET'])
@login_required
@roles_accepted('audit')
def yeartree_only(uuid=None):
    uuid = request.args.get('uuid', None)
    if uuid is None:
        return render_template('/graph/yeartree.html', famtree_data='')

    famtree = FamTree().get(uuid)
    return render_template('/graph/yeartree.html', famtree_data=json.dumps(famtree))
