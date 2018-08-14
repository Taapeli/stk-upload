#!/usr/bin/env python3
"""
RESI-tägien yhdistäminen

1 RESI
2 PLAC Viljakkala
2 DATE FROM 1865 TO 1871
1 RESI
2 PLAC Viljakkala
2 DATE FROM 1865 TO 1871
1 RESI
2 PLAC Viljakkala
2 DATE FROM 1865 TO 1871
1 RESI
2 PLAC Viljakkala
2 DATE FROM 1865 TO 1871
1 RESI
2 PLAC Viljakkala
2 DATE FROM 1858 TO 1864

--->

1 RESI
2 PLAC Viljakkala
2 DATE FROM 1858 TO 1871

"""
version = "0.1"

from collections import defaultdict


class Daterange:
    def __init__(self,start,end):
        self.start = start
        self.end = end
    def __repr__(self):
        if self.start == self.end:
            return "%s" % self.start
        else:
            return "FROM %s TO %s" % (self.start,self.end)
    
class Dateranges:
    def __init__(self):
        self.ranges = []
    def __repr__(self):
        return repr(self.ranges)
    def xxxadd(self,newrange):
        for r in self.ranges:
            if newrange.end >= r.start-1 and newrange.start <= r.end+1:
                r.start = min(r.start,newrange.start)
                r.end = max(r.end,newrange.end)
                return
        self.ranges.append(newrange)
        self.ranges.sort(key=lambda r: r.start)

    def add(self,newrange):
        self.ranges.append(newrange)
        self.ranges.sort(key=lambda r: r.start)
        self.ranges = self.merge(self.ranges)
    def merge(self,ranges):        
        if len(ranges) <= 1: return ranges
        # assert: at least 2 ranges in ranges
        # assert: ranges is sorted according to range.start
        r0 = ranges[0]
        r1 = ranges[1]
        if r1.start <= r0.end+1: # merge r0 and r1
            r0.end = max(r0.end,r1.end)
            return self.merge([r0] + ranges[2:])
        else:
            return [r0] + self.merge(ranges[1:])
        
        

places = defaultdict(lambda: defaultdict(Dateranges))  # places[indi][place] = [daterange,daterange,...]

def add_args(parser):
    pass

def initialize(run_args):
    pass

def phase1(run_args, gedline):
    global place
    if gedline.path.endswith(".RESI.PLAC"):
        indi_id = gedline.path.split(".")[0]
        place = gedline.value
    if gedline.path.endswith(".RESI.DATE"):
        indi_id = gedline.path.split(".")[0]
        date = gedline.value
        if date.isdigit():
            newrange = Daterange(int(date),int(date))
        else:
            parts = date.split() # from yyyy to yyyy
            y1 = int(parts[1])
            y2 = int(parts[3])
            newrange = Daterange(y1,y2)
        places[indi_id][place].add(newrange)

def phase2(run_args):
    pass

def phase3(run_args, gedline,f):
    parts = gedline.path.split(".")
    indi_id = parts[0]
    if len(parts) > 1 and parts[1] == "RESI":
        if indi_id not in places: return
        placelist = places[indi_id]
        for placename in placelist:
            for daterange in placelist[placename].ranges:
                f.emit("1 RESI")
                f.emit("2 PLAC " + placename)
                f.emit("2 DATE %s" % daterange)
        del places[indi_id]
        return
    gedline.emit(f)

def main():
    ranges = Dateranges()
    ranges.add( Daterange(1,5) )
    ranges.add( Daterange(2,6) )
    ranges.add( Daterange(8,15) )
    ranges.add( Daterange(8,10) )
    print(ranges)

    ranges = Dateranges()
    ranges.add( Daterange(1,5) )
    ranges.add( Daterange(8,15) )
    ranges.add( Daterange(2,6) )
    print(ranges)

    ranges = Dateranges()
    ranges.add( Daterange(10,15) )
    ranges.add( Daterange(5,9) )
    ranges.add( Daterange(1,4) )
    print(ranges)

if __name__ == "__main__":
    main()
