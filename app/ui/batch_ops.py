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

'''
Created on 23.9.2021

@author: jm
'''
from flask_babelex import _
from bl.batch.root import State

# List of functions available for researcher

RESEARCHER_FUNCTIONS = [ # (URL, title)
    ("/scene/material/batch?state={state}&batch_id={batch_id}", 
     "Browse this material"),
    ("/audit/user/request/{batch_id}",     _("Send for auditing")),
    ("/audit/user/withdraw/{batch_id}",    _("Withdraw auditing")),
    ("/gramps/batch_download/{batch_id}",  _("Download the Gramps file")),
    ("/gramps/show_upload_log/{batch_id}", _("Show upload log")),
    ("/gramps/gramps_analyze/{batch_id}",  _("Gramps Verify Tool")),
    ("/gramps/batch_delete/{batch_id}",    _("Delete from database")),
    ]

# A boolean vector, which RESEARCHER_FUNCTIONS are allowed for any Root.status

RESEARCHER_OPERATIONS = { #    browse     request   withdraw  download log     verify  delete
    State.ROOT_UNKNOWN:        (False,    False,    False,    False,   True,   False,   True),
    State.FILE_LOADING:        (False,    False,    False,    False,   True,   False,   True),
    State.FILE_LOAD_FAILED:    (True,     False,    False,    True,    True,   False,   True),                                                  
    State.ROOT_STORING:        (False,    False,    False,    True,    True,   True,    True),
    State.ROOT_CANDIDATE:      (True,     True,     False,    True,    True,   True,    True),
    State.ROOT_REJECTED:       (True,     False,    False,    True,    True,   True,    True),
    State.ROOT_AUDIT_REQUESTED:(True,     False,    True,     True,    True,   True,    True),
    State.ROOT_AUDITING:       (True,     False,    True,     True,    True,   True,    True),
    State.ROOT_ACCEPTED:       (True,     False,    False,    True,    True,   True,    False),
    }

