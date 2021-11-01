from bl.base import Status, StkEncoder
from bl.source import SourceReader, SourceWriter

from .. import bp

from flask import request, session as user_session, render_template
from flask_security import current_user, roles_accepted

from ui.user_context import UserContext
import shareds

@bp.route("/merge/sources")
@roles_accepted('audit')
def index():
    fname = "merge_sources.html"
    return render_template(fname)

@bp.route('/merge/sources/list')
@roles_accepted('audit')
def list_sources(series=None):
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    u_context.set_scope_from_request(request, 'merge_sources_scope')
    u_context.count = request.args.get('c', 100, type=int)

    with SourceReader("read", u_context) as reader: 
        if series:
            u_context.series = series
        try:
            results = reader.get_source_list()
        except KeyError as e:
            results = {}
            results['status'] = Status.ERROR
            results['errorText'] = str(e)
        return StkEncoder.jsonify(results)



@bp.route('/merge/sources/get/<uuid1>')
@roles_accepted('audit')
def getsource(uuid1):
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    with SourceReader("read", u_context) as reader: 
        try:
            results = reader.get_source_with_references(uuid1, u_context)
        except KeyError as e:
            results = {}
            results['status'] = Status.ERROR
            results['errorText'] = str(e)
        return StkEncoder.jsonify(results)

@bp.route('/merge/sources/merge/<int:id1>/<int:id2>')
@roles_accepted('audit')
def merge_sources(id1, id2):
    # Set context by owner and the data selections
    u_context = UserContext(user_session, current_user, request)
    # Which range of data is shown
    with SourceWriter("update", u_context) as writer: 
        try:
            results = writer.mergesources(id1, id2)
        except KeyError as e:
            results = {}
            results['status'] = Status.ERROR
            results['errorText'] = str(e)
        return StkEncoder.jsonify(results)
