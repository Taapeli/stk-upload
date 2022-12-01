#!/usr/bin/env python3

import json
import sys
import os
import sys
import time

from pathlib import Path

from gramps.gen.lib import Attribute

from gi.repository import Gtk, Gdk, GObject

from gramps.gen.db import DbTxn
from gramps.gen.lib import Note

from gramps.gui.plug import tool

  
#------------------------------------------------------------------------
#
# Tool
#
#------------------------------------------------------------------------
class Tool(tool.Tool):

    def __init__(self, dbstate, user, options_class, name, callback=None):
        self.user = user
        self.dbstate = dbstate
        self.uistate = user.uistate
        self.db = self.dbstate.db
        tool.Tool.__init__(self, dbstate, options_class, name)

        self.batch_id = self.options.handler.options_dict["batch_id"]
        self.basedir = self.options.handler.options_dict["basedir"]

        saved_path = sys.path[:]
        try:
            instance_dir = Path(self.basedir) / "instance"
            print("instance_dir",instance_dir)
            sys.path.append(str(instance_dir))
            import config
        finally:
            sys.path = saved_path

        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(
                config.NEO4J_URI,
                auth = (config.NEO4J_USERNAME, config.NEO4J_PASSWORD),
                connection_timeout = 15) 
        print(self.driver)

        self.values = {}
        
        self.do_objtype('Person',        self.db.iter_people)
        self.do_objtype('Family',        self.db.iter_families)
        self.do_objtype('Event',         self.db.iter_events)
        self.do_objtype('Place',         self.db.iter_places)
        self.do_objtype('Citation',      self.db.iter_citations)
        self.do_objtype('Source',        self.db.iter_sources)
        self.do_objtype('Repository',    self.db.iter_repositories)
        self.do_objtype('Media',         self.db.iter_media)
        self.do_objtype('Note',          self.db.iter_notes)

        cypher = "match (r:Root{id:$batch_id}) return r"
        print("cypher:", cypher)        
        print("batch_id:", self.batch_id)        
        rec = self.driver.session().run(cypher, batch_id=self.batch_id).single()
        root = rec["r"]
        print(root)

        n = Note()
        n.set_gramps_id("Isotammi-IDs")
        n.set_type("Isotammi metadata")
        data = {
            "date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
            "batch_id": self.batch_id,
            "ids": self.values,
            "file": root["xmlname"]
        }
        s = json.dumps(data, indent=2)
        print("JSON length:", len(s))
        print("Num items:", len(self.values))
        n.set(s)
        with DbTxn("Adding Isotammi-IDs note", self.db) as trans:
            notehandle = self.db.add_note(n, trans)
        print("Done")


    def do_objtype(self, objtype, iterfunc):
        ids = {}
        num_objs = 0
        num_objs1 = 0
        num_objs2 = 0
        self.values[objtype] = {}
        cypher = "match (r:Root{id:$batch_id}) --> (p:%s) return p" % objtype
        print("cypher:", cypher)        
        print("batch_id:", self.batch_id)        
        for rec in self.driver.session().run(cypher, batch_id=self.batch_id):
            gramps_id = rec["p"]["id"]
            isotammi_id = rec["p"]["iid"]
            ids[gramps_id] = isotammi_id
            num_objs1 += 1
        print("- isotammi-ids:",objtype,num_objs1)
        for obj in iterfunc():
            num_objs2 += 1
            iid = ids.get(obj.gramps_id)
            if iid:
                self.values[objtype][obj.handle] = iid
                num_objs += 1
        print("- isotammi-ids:",objtype,num_objs,"/",num_objs2)
        print("M:",objtype,num_objs)
        return num_objs

#------------------------------------------------------------------------
#
# Options
#
#------------------------------------------------------------------------
class Options(tool.ToolOptions):
    """
    Define options and provides handling interface.
    """

    def __init__(self, name, person_id=None):
        tool.ToolOptions.__init__(self, name, person_id)
        self.options_dict = {
            "batch_id": "",
            "basedir": "",
        }
        self.options_help = {
            "batch_id": ("=str", "Batch ID", "String"),
            "basedir": ("=str", "Current directory", "String"),
        }

        
