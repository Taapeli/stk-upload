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

#!/usr/bin/env python3
"""
Restores marked tags: <tag>-X -> <tag>
"""

version = "2.0"
#doclink = "http://wiki.isotammi.net/wiki/Gedcom:Gedcom-Marriages-ohjelma"

from flask_babelex import _
name = _("Unmark")
docline = _("Restores marked tags: <tag>-X -> <tag>")
doclinks = {
    'fi': "http://wiki.isotammi.net/wiki/Poista_tag_X_merkinnät", 
}    

from .. import transformer

def add_args(parser):
    pass

def initialize(options):
    return Unmark()

class Unmark(transformer.Transformation):
    def transform(self,item,options,phase):
        # phase 1
        if item.tag.endswith("-X"):
            item.tag = item.tag[0:-2]
            return item
        return True
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
