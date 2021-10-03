'''
Created on 23.9.2021

@author: jm
'''
from flask_babelex import _
from bl.root import State

# List of functions available for researcher

RESEARCHER_FUNCTIONS = [ # (URL, title)
    ("/scene/persons/search?set_scope=1&batch_id=", "Browse this material"),
    ("/audit/user/request/",     _("Send for auditing")),
    ("/audit/user/withdraw/",    _("Withdraw auditing")),
    ("/gramps/batch_download/",  _("Download the Gramps file")),
    ("/gramps/show_upload_log/", _("Show upload log")),
    ("/gramps/batch_delete/",    _("Delete from database")),
    ]

# A boolean vector, which RESEARCHER_FUNCTIONS are allowed for any Root.status

RESEARCHER_OPERATIONS = { #    browse     request   withdraw  download log     delete
    State.ROOT_UNKNOWN:        (False,    False,    False,    False,   True,    True),
    State.FILE_LOADING:        (False,    False,    False,    False,   False,   False),
    #State.FILE_LOAD_FAILED:   (No Root node),
    State.ROOT_STORING :       (False,    False,    False,    True,    True,    False),
    State.ROOT_CANDIDATE:      (True,     True,     False,    True,    True,    True),
    State.ROOT_REJECTED:       (True,     False,    False,    True,    True,    True),
    State.ROOT_AUDIT_REQUESTED:(True,     False,    True,     True,    True,    True),
    State.ROOT_AUDITING:       (True,     False,    False,    True,    True,    True),
    State.ROOT_ACCEPTED:       (True,     False,    False,    True,    True,    False),
    }

