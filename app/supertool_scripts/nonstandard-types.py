import os
from pprint import pprint

from gramps.gen.lib import AttributeType
from gramps.gen.lib import ChildRefType
from gramps.gen.lib import EventRoleType 
from gramps.gen.lib import EventType
from gramps.gen.lib import FamilyRelType
from gramps.gen.lib import NameType
from gramps.gen.lib import NameOriginType
from gramps.gen.lib import PlaceType
from gramps.gen.lib import RepositoryType
from gramps.gen.lib import SourceMediaType
from gramps.gen.lib import SrcAttributeType

types = defaultdict(lambda:defaultdict(int))

WHITELIST_DIR = "instance/whitelists"

def nonstandard_types():
    print(" epästandardit tyypit.py")
    for p in db.iter_people():
        #print(p)
        check_attributes(p)
        scan_events(p)
        scan_media(p)
        scan_names(p)
    for obj in db.iter_families():
        objtype = obj.get_relationship()
        check(obj, objtype, "", FamilyRelType)
        for childref in obj.get_child_ref_list():
            check(obj, childref.get_mother_relation(), "childref", ChildRefType)
            check(obj, childref.get_father_relation(), "childref", ChildRefType)
        scan_events(obj)
        check_attributes(obj)
        scan_media(obj)
    for e in db.iter_events():
        etype = e.get_type()
        check(e, etype, "", EventType)
        check_attributes(e)
        scan_media(obj)
    for p in db.iter_places():
        ptype = p.get_type()
        check(p, ptype, "", PlaceType)
        scan_media(obj)
    for obj in db.iter_citations():
        scan_media(obj)
    for obj in db.iter_sources():
        for a in obj.get_attribute_list():  # SrcAttribute
            atype = a.get_type()
            check(obj, atype, "attr", SrcAttributeType)
        for reporef in obj.get_reporef_list():  
            mediatype = reporef.get_media_type()
            check(obj, mediatype, "mediatype", SourceMediaType)
        scan_media(obj)
    for r in db.iter_repositories():
        rtype = r.get_type()
        check(r, rtype, "", RepositoryType)
    for m in db.iter_media():
        check_attributes(m)

    show_results()
    print(PlaceType._S2IMAP)
    print(SourceMediaType._S2IMAP)

    return 123

def epästandardit_tyypit2():
    print(" epästandardit tyypit.py")
    for func in [
        db.iter_people,
        db.iter_families,
        db.iter_events,
        db.iter_places,
        db.iter_citations,
        db.iter_sources,
        db.iter_repositories,
        db.iter_media,
        db.iter_notes
    ]:
        for obj in func():
            scan(obj)
    show_results()
    return 345
    
def scan(obj):
    if hasattr(obj, "get_attribute_list"):
        check_attributes(obj)
    if hasattr(obj, "get_event_ref_list"):
        scan_events(obj)
    if hasattr(obj, "get_media_list"):
        scan_media(obj)
    if hasattr(obj, "get_primary_name"):
        scan_names(obj)
    if hasattr(obj, "get_reporef_list"):
        scan_names(obj)
        

def check_attributes(obj):
    for a in obj.get_attribute_list():
        atype = a.get_type()
        check(obj, atype, "attr", AttributeType)

def check(obj, objtype, name, TypeClass):
    value = objtype.serialize()
    classname = TypeClass.__name__
    standard_values = get_standard_values(TypeClass)
    typename = objtype.xml_str()
    if classname.startswith("EventRole"):
        print("standard_values",standard_values)
        print("objtype",typename)
    if typename not in standard_values:
        types[classname][typename] += 1
    return
    if value[0] == TypeClass.CUSTOM:
        #print(TypeClass._S2IMAP)
        intvalue = TypeClass._S2IMAP.get(value[1])
        if intvalue is not None:
            t = TypeClass(intvalue)
            print(obj.gramps_id, name, value, intvalue, str(t), t.serialize(), t.xml_str())
        types[TypeClass][value[1]] += 1

def get_standard_values(TypeClass):
    classname = TypeClass.__name__
    name = classname.replace("Type","")
    basedir = args
    fname = basedir + "/" + WHITELIST_DIR + "/" + name
    if os.path.exists(fname):
        return [line.strip() for line in open(fname).readlines() if line.strip() != ""]
    else:
        res = []
        for _,_,name in TypeClass._DATAMAP:
            if name == "Unknown": continue
            if name == "Custom": continue
            res.append(name)
        res.sort()
        with open(fname,"w") as f:
            for name in res:
                print(name, file=f)
        return res
    
def scan_events(p):
    for er in p.get_event_ref_list():
        ertype = er.get_role()
        check(p, ertype, "eventrole", EventRoleType)
        check_attributes(er)

def scan_media(obj):
    for mediaref in obj.get_media_list():
        check_attributes(mediaref)

def scan_names(p):
    for nameobj in [p.get_primary_name()] + p.get_alternate_names():
        check(p, nameobj.get_type(), "", NameType)
        for surname in nameobj.get_surname_list():
            check(p, surname.get_origintype(), "nameorigintype", NameOriginType)
            

def show_results():
    for typeclass, values in types.items():
        print()
        print(typeclass)
        #pprint(dict(values))
        for value, count in values.items():
            print("-",value,count)
            result.add_row([typeclass,value,count])
    print()
    print(len(types),"types")
    
