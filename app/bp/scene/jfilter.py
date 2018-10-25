'''
Created on 21.10.2018

@author: jm

'''
import sys
sys.path = sys.path[1:]
#print(sys.path)
from models.gen.citation import Citation
from models.gen.source import Source


def link_cite(citation_ref, obj, cits):
    '''
    Sivulla esiintyvät sitaatit kootaan listaan cits kutsulla
        macro.link_cite(person.citation_ref, obj, cits)
    Makron tulee
        1) muodostaa viite_src "1a", "1b", "2a" ... jossa parit
           (Repository_id, Source_id) vastavat numeroita ja 
           Citation_id:t kirjaimia
           - jos viite on jo taulukossa cits, käytetään sitä
           - muuten luodaan uusi:
        2) tallettaa listaan cits[] tuplet 
           esim. cits[0] = ((100269,91355), ("1a", 92125))
           - avain i = (Repository_id, Source_id)
           - arvo j = (viite_str, Citation_id)
        3) palauttaa sivun esiintymispaikkaan linkin
            <a href="viite_str" title="Source_name">viite_str</a>
    '''
    if citation_ref:
        for c in citation_ref:
            cid = c.uniq_id
            if c.source.repo_ref:
                rid = c.source.repo_ref[0]
            else:
                rid = None
            sid = c.source.uniq_id
            print("repository {}, source {}, citation {}".format(rid, sid, cid))
            # Etsi, onko viite jo olemassa 
            x = (rid, cid)
            ref = "1a"
            ind0 = -1
            ind1 = -1
            for i in cits:
                if cits[i][0] == x:
                    ind0 = i   #löytyi {{i}}: cits[i][1]
            # Muodosta uusi viite
            if ind0 < 0:
                value = ''
            # Talleta viite cits-taulukkoon
            # Näytä viite ja linkki
            out =""
            if c.source.repo_ref:
                r = obj[c.source.repo_ref]
                out += "<i>{}</i>\n".format(r.rname)
            out += '<a href="#ref{}>'.format(ref)
            out += '{}<br>&nbsp;&ndash; {}</a>'.format(c.source.stitle, c.page)
    return "({}, {}) = {}\n{}".format(rid, sid, cid, out)

if __name__ == '__main__':
    
    cits = []
    #TODO: obj[c.source.repo_ref] ja c.source.stitle, c.page piää määritellä!
    obj = dict([
        (76982, "I0001"),
        (77034, "C0000"),
        (77032, "S0000"),
        (76901, "R0000"),
        (76904, "E0004"),
        (76961, "C0000"),
        (76921, "I0000"),
        (77036, "C0002"),
        (76962, "C0002"),
        (76957, "S0000") ])
    data = ((76978,77032,77036),
            (76978,77032,77034),
            (76978,77032,77034),
            (76978,77032,76962),
            (76978,77032,76961),
            (76978,77032,76961),
            (76978,76957,77036),
            (76978,76957,77034),
            (76978,76957,77034),
            (76978,76957,76962))
    for r, s, c in data:
        cita = Citation()
        cita.uniq_id = c
        cita.source = Source()
        cita.source.uniq_id = s
        cita.source.repo_ref.append(r)
  
        print(link_cite([cita], obj, cits))
        print(cits)

    print("Done {} references".format(len(cits)))
