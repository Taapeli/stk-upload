# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 27.1.2016

def karajat_loader(pathname):
    """ Lukee csv-tiedostosta referenssinimet
        Syöte: ['Pk-nr','Käräjätyyppi','Käräjäpaikka','Vuosi','Kuid','Jakso']
        Tyyppi:  int     str            str            int     int    int
        
        Vastaava dokumentti on http://digi.narc.fi/digi/view.ka?kuid={{kuid}}
    """
    rivit = []
    row_nro = 0
    tyhjia = 0

    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        reader=csv.reader(f, dialect='excel')
        # Tarkastetaan ja ohitetaan otsikkorivi
        row = reader.__next__()
        if row.__len__ != 6 and row[0] != "Pk-nr":
            raise KeyError('Väärät sarakeotsikot: ' + str(row))
       
        for row in reader:
            row_nro += 1
            rid = (u'K%05d' % row_nro)
            nimi=row[0].strip()
            if row[0].__len__() == 0:
                tyhjia += 1
                continue # Tyhjä nimi ohitetaan
            
            ref=row[1]
            on_ref=(row[2].lower().startswith('k'))
            source=row[3]
            if row[4].startswith('m'):
                sp = 'M'
            elif row[4].startswith('n'):
                sp = 'F'
            else:
                sp = ''

            # Luodaan rivitieto tulostettavaksi
            rivi = dict( \
                oid=rid, \
                nimi=nimi, \
                refnimi=ref, \
                onref=on_ref, \
                source=source, \
                sp=sp )
            rivit.append(rivi)
    
    logging.info(u'%s: %d riviä, %d tyhjää' % (pathname, row_nro, tyhjia))
    return (rivit)




# Testaa referenssinimet
# python3 models/datareader.py tiedosto.csv > lst

import sys
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Käyttö: " + sys.argv[0] + " tiedosto.csv", file=sys.stderr)
        exit(1)
        
    rivit = karajat_loader(sys.argv[1])
    for r in rivit:
        print("{0}: {1:20s}{2:20s}{3} {4:1s} ({5:s})".format( r['oid'],
            r['nimi'], r['refnimi'], r['onref'], r['sp'], r['source']) )
