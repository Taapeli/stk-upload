import transformer

def initialize(options):
    return InfoParser()

class Info:
    gedcom_version = None
    submitter = None
    charset = None
    source_program = None
    source_program_version = None
    num_individuals = 0
    num_families = 0
    num_notes = 0
    num_sources = 0
    num_repos = 0
    num_multimedia = 0
        
class InfoParser(transformer.Transformation):
    def __init__(self):
        self.info = Info()
    def transform(self,item,options,phase):
        #print(item.path,item.value)
        if item.level == 0:
            if item.value == "INDI":
                self.info.num_individuals += 1
            if item.value == "FAM":
                self.info.num_families += 1
            if item.value == "NOTE":
                self.info.num_notes += 1
            if item.value == "SOUR":
                self.info.num_sources += 1
            if item.value == "REPO":
                self.info.num_repos += 1
            if item.value == "OBJE":
                self.info.num_multimedia += 1
            return True
        if item.path == "HEAD.CHAR":
            self.info.charset = item.value
        if item.path == "HEAD.GEDC.VERS":
            self.info.gedcom_version = item.value
        if item.path == "HEAD.SOUR":
            self.info.source_program = item.value
        if item.path == "HEAD.SOUR.VERS":
            self.info.source_program_version = item.value
        if item.path.endswith(".SUBM.NAME"):
            self.info.submitter = item.value
            
        return True

