import transformer

def initialize(options):
    return InfoParser()

class Info: 
    gedcom_version = None
    submitter = None
    charset = None
    date = ""
    time = ""
    source_program = None
    source_program_version = None 
    num_individuals = 0
    num_families = 0
    num_places = 0
    num_notes = 0
    num_sources = 0
    num_citations = 0
    num_repos = 0
    num_multimedia = 0
        
class InfoParser(transformer.Transformation):
    def __init__(self):
        self.info = Info()
        self.places = set()
        self.submitter_xref = None
        
    def transform(self,item,options,phase):
        #print(item.path,item.value)
        if item.level == 0:
            if item.tag == "INDI":
                self.info.num_individuals += 1
            if item.tag == "FAM":
                self.info.num_families += 1
            if item.tag == "NOTE":
                self.info.num_notes += 1
            if item.tag == "SOUR":
                self.info.num_sources += 1
            if item.tag == "REPO":
                self.info.num_repos += 1
            if item.tag == "OBJE":
                self.info.num_multimedia += 1
            return None
        xref = None
        if item.path[0] == '@': xref = item.path.split(".")[0]
        if item.tag == "NOTE":
            self.info.num_notes += 1
        if item.tag == "SOUR":
            self.info.num_citations += 1
        if item.tag == "PLAC":
            self.places.add(item.value)
            self.info.num_places = len(self.places)
        if item.path == "HEAD.SUBM":
            self.submitter_xref = item.value
        if item.path == "HEAD.CHAR":
            self.info.charset = item.value
        if item.path == "HEAD.DATE":
            self.info.date = item.value
        if item.path == "HEAD.DATE.TIME":
            self.info.time = item.value
        if item.path == "HEAD.GEDC.VERS":
            self.info.gedcom_version = item.value
        if item.path == "HEAD.SOUR":
            self.info.source_program = item.value
        if item.path == "HEAD.SOUR.VERS":
            self.info.source_program_version = item.value
        if item.path == "HEAD.SOUR.NAME":
            self.info.source_program_name = item.value
        if item.path.endswith(".SUBM.NAME") and xref == self.submitter_xref: 
            self.info.submitter = item.value
            
        return None

