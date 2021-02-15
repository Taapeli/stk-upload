#   Isotammi Geneological Service for combining multiple researchers' results.
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
Extracted from bp.gedcom.routes on 21.6.2019 by jm

@author Kari Kujansuu <kari.kujansuu@gmail.com>
@author: jm
'''

import sys
import os
import io
import importlib
import traceback
from argparse import ArgumentParser

from flask_babelex import _, ngettext

import logging 
from bp.gedcom.models import gedcom_utils
LOG = logging.getLogger(__name__)

from models import util
from ..transforms.model.ged_output import Output
from .. import transformer


def process_gedcom(arglist, transform_module):
    """ Implements a mechanism for Gedcom transforms.
    
    Returns a dictionary:
        - stdout        result texts for the user log page
        - stderr        errors texts for the user log page 
        - oldname       original name of gedcom file
        - logfile       log file name

    The transform_module is assumed to contain the following methods:
    - initialize
    - transform: implements the actual transformation for a single line block ("item")
    - fixlines: preprocesses the Gedcom contents (list of lines/strings)
    - add_args: adds the transform-specific arguments (ArgumentParser style)

    See sukujutut.py as an example
    """

    msg = _("Transform '{}' started at {}").format(transform_module.name, util.format_timestamp())
    LOG.info(f"------ {msg} ------")

    parser = ArgumentParser()
#    parser.add_argument('transform', help="Name of the transform (Python module)")
    parser.add_argument('input_gedcom', help=_("Name of the input GEDCOM file"))
    parser.add_argument('--logfile', help=_("Name of the log file"), default="_LOGFILE" )
#    parser.add_argument('--output_gedcom', help="Name of the output GEDCOM file; this file will be created/overwritten" )
    parser.add_argument('--display-changes', action='store_true',
                        help=_('Display changed rows'))
    parser.add_argument('--dryrun', action='store_true',
                        help=_('Do not produce an output file'))
    parser.add_argument('--nolog', action='store_true',
                        help=_('Do not produce a log in the output file'))
    parser.add_argument('--encoding', type=str, default="UTF-8", 
                        choices=["UTF-8", "UTF-8-SIG", "ISO8859-1"],
                        help=_("Encoding of the input GEDCOM"))
    transform_module.add_args(parser)
    args = parser.parse_args(arglist)
    args.output_gedcom = None
    args.nolog = True # replaced by history file
    gedcom_utils.history_append(args.input_gedcom, "\n"+msg)
    gedcom_utils.history_append_args(args)

    # You may deny stdout redirect by setting GEDCOM_REDIRECT_SYSOUT=False in config.py
    if not 'GEDCOM_REDIRECT_SYSOUT' in globals():
        GEDCOM_REDIRECT_SYSOUT = True
    try:
        gedcom_utils.init_log(args.logfile)
        with Output(args) as out:
            out.original_line = None
            out.transform_name = transform_module.__name__
            if GEDCOM_REDIRECT_SYSOUT:
                saved_stdout = sys.stdout
                saved_stderr = sys.stderr
                sys.stdout = io.StringIO()
                sys.stderr = io.StringIO()
            if args.dryrun:
                old_name = ""
            else:
                old_name = out.new_name

            print(f"<h3>------ {msg} ------</h3>")
            t = transformer.Transformer(transform_module=transform_module,
                                        display_callback=gedcom_utils.display_changes,
                                        options=args)
            """ Create a Gedcom transformer g from Transformer t and execute
                the transformations.
                
                The resulting Items are in the list g.items 
            """
            g = t.transform_file(args.input_gedcom) 
            g.print_items(out)
            print("<div>")
            print("<b>------ " + 
                  ngettext("Total {num} change", "Total {num} changes", 
                           num=t.num_changes).format(num=t.num_changes) +
                  "</b>")
            #print(_("------ Number of changes: {}").format(t.num_changes))
    except:
        traceback.print_exc()
    finally:
        if old_name: 
            gedcom_utils.history_append(args.input_gedcom, 
                                        _('File saved as {}').format(args.input_gedcom))
            gedcom_utils.history_append(args.input_gedcom, 
                                        _("Old file saved as {}").format(old_name))
        else:
            gedcom_utils.history_append(args.input_gedcom, 
                                        _("File saved as {}").format(args.input_gedcom + "temp"))
            msg = _("Transform '{}' ended at {}").format(transform_module.name,
                                                         util.format_timestamp())
        gedcom_utils.history_append(args.input_gedcom, msg)
        print(f"<h3>------ {msg} ------</h3>")
        print("</div>")
        output = None
        errors = None
        if GEDCOM_REDIRECT_SYSOUT:
            output = sys.stdout.getvalue()
            errors = sys.stderr.getvalue()
            sys.stdout = saved_stdout
            sys.stderr = saved_stderr
    if old_name:
        old_basename = os.path.basename(old_name)
    else:
        old_basename = ""
    if errors and old_basename:
        os.rename(old_name, args.input_gedcom)
        old_basename = "" 
    rsp = dict(stdout=output, stderr=errors, oldname=old_basename, logfile=args.logfile)
    if hasattr(transform_module, "output_format") \
       and transform_module.output_format == "plain_text":
        rsp["plain_text"] = True
    return rsp


def build_parser(filename, _gedcom, _gedcom_filename):
    ''' Returns transformation module and parser options list.
    '''
    modname = filename[:-3]
    transform_module = importlib.import_module("bp.gedcom.transforms."+modname)
    logging.info(f'Transformer {modname} {transform_module.version} for {_gedcom}')

    class Arg:
        def __init__(self, name, name2, action, atype, choices, default, ahelp):
            self.name = name
            self.name2 = name2
            self.action = action
            self.type = atype
            self.choices = choices
            self.default = default
            self.help = ahelp
        def __str__(self):
            return f'{self.name} {self.help}'

    class Parser:
        ''' Defines Gedcom parser command with options.
        '''
        def __init__(self):
            self.args = []
        def add_argument(self, name, name2=None, action='store', 
                         type=str,  # @ReservedAssignment
                         default=None, 
                         help=None, # @ReservedAssignment
                         nargs=0,   # @UnusedVariable 
                         choices=None):  
            self.args.append(Arg(name, name2, action, type, choices, 
                                 default, help))
             
        def generate_option_rows(self):
            rows = []
            class Row: pass
            for arg in self.args:
                row = Row()
                row.name = arg.name
                row.action = arg.action
                row.help = arg.help
                row.checked = ""
                row.classname = "transform_option"
                if arg.action == 'store_true':
                    row.type = "checkbox"
                    if row.name == "--dryrun": row.checked = "checked"
                    if row.name == "--display-changes": 
                        row.checked = "checked"
                        row.classname = "display_option"
                    elif row.name == "--display_all_unique_places": 
                        row.classname = "clear_others"
                elif arg.action == 'store_false':
                    row.type = "checkbox"
                elif arg.action == 'store_const':
                    row.type = "checkbox"
                elif arg.choices:
                    row.type = "select"
                    row.choices = arg.choices
                elif arg.action == 'store' or arg.action is None:
                    row.type = 'text'
                    if arg.type == int:
                        row.type = 'number'
                elif arg.action == 'append':
                    row.type = 'text'
                elif arg.type == str:
                    row.type = 'text'
                elif arg.type == int:
                    row.type = 'number'
                else:
                    raise RuntimeError(_("Unsupported type: "), arg.type )
                rows.append(row)
            return rows

        def build_command(self, argdict):
            return " ".join(self.build_command_args(argdict))
            
        def build_command_args(self, argdict):
            args = []
            for arg in self.args:
                if arg.name in argdict:
                    value = argdict[arg.name].rstrip()
                    if not value: 
                        value = arg.default
                    if value: 
                        if arg.action in {'store_true', 'store_false'} \
                           and value == "on": 
                            value = ""
                        if arg.name[0] == "-":
                            args.append(arg.name)
                            if value: 
                                args.append(value)
                        else:
                            args.append(value)
            args.append("--dryrun")
            args.append("--nolog")
            return args

    parser = Parser()

    parser.add_argument('--display-changes', action='store_true',
                        help=_('Display changed rows'))
    
    transform_module.add_args(parser)

    return transform_module, parser

