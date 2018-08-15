import sys


"""
Kari Kujansuu <kari.kujansuu@gmail.com>
	
ma 2. heinäk. 12.56
	
-> Pekka, Timo, Juha, Juha, Jorma
Kommentteja näihin (punaisella):

Group: -
   Coding:  original = ANSI -> UTF-8 - pitää siis vaihtaa CHAR-tägi sekä itse datan koodaus
Group: 1.1
   Lines with nbr. and missing tag insert tag "_DUMMY" eikö näitä voi samantien poistaa?
   Modify lines without nbr. + tag: Concatenate to previous line - parempi lisätä CONT-rivi, koska yleensä johtuu rivinvaihdosta edellisen rivin sisällössa
   Concatenate CONC to previous line Gedcomin rivin maksimipituus on 255 joten ei tätä aina voi tehdä - kannattaako tehdä koskaan?
Group: 1.2
      Delete orphan records Consolidate multiple identical records - mahdollista mutta työlästä - onko näitä usein?
Group: 2.1
   Delete line blocks ending with ...:
     "1 NOTE" tässä tarkoitetaan yksittäisiä tyhjiä NOTEja, joilla ei ole jatkorivejä (CONC/CONT)
   Delete line block with text check ...:
     "1 EVEN" tarkoitetaan ehkä tyhjää EVEN-rakennetta?
   Delete lines starting with ...:
     "3 SOUR"
     "2 GIVN"
     "2 SURN"
     "3 REFN"
     "1 STAT"
     "3 NOTE"
   Delete lines ending with ...:
     "1 NOTE" tämä varmaan sama kuin aiemmin (tyhjä NOTE)?
Group: 2.2
   Delete empty CONC/CONT lines tyhjiä CONT-rivejä ei voi poistaa - ne merkitsevät tyhjää riviä esim. NOTEn sisällä
   Delete spaces at line end ei saa tehdä ainakaan tägeille NOTE,TEXT,CONT,CONC
   Delete multiple spaces miksi?
   Delete empty DATE + DATE ? lines ok
   Delete multiple identical lines siis peräkkäiset identtiset rivit, paitsi CONT/CONC-rivit
Group: 3.3
   Date BET YYYY AND Y > BET YYYY AND YYYY
   Correct missing year in date range
Group: 5.1 näitä täytyy katsoa tarkemmin sitten kun saan malliksi Sukujutut-gedcomin jossa näitä tilanteita esiintyy
   "Move text":
     "1 NOTE %1#2 SOUR %2" -> "1 NOTE %1"
     "1 ADDR %1" -> "1 ADDR#2 ADR1 %1" eikös alkuperäinen (1 ADDR ...) ole ihan OK?
     "1 EVEN#2 TYPE Ei_julkaista#2 PLAC %1" -> "1 EVEN#2 TYPE Ei_julkaista#2 NOTE %1"
     "1 EMIG" -> "1 RESI"
     "1 EVEN#2 TYPE Kummit#2 PLAC %1" -> "1 EVEN#2 TYPE Kummit#2 NOTE Description: %1"
     "1 EVEN#2 TYPE Tutkijan omat#2 PLAC %1" -> "1 EVEN#2 TYPE Tutkijan omat#2 NOTE %1"
     "1 EVEN#2 TYPE Kolmonen" -> "1 NOTE Kolmonen"
     "1 EVEN#2 TYPE Kaksonen" -> "1 NOTE Kaksonen"


---------------
Lisää kommentteja Liisa Ahosen gedcomin perusteella:


Group: -
   Coding:  original = ANSI -> UTF-8 - pitää siis vaihtaa CHAR-tägi sekä itse datan koodaus
   OK
   
Group: 1.1
   Lines with nbr. and missing tag insert tag "_DUMMY" eikö näitä voi samantien poistaa?
   Ahosen aineistossa ei ole tällaisia, joten ei toteutetttu
   
   Modify lines without nbr. + tag: Concatenate to previous line - parempi lisätä CONT-rivi, koska yleensä johtuu rivinvaihdosta edellisen rivin sisällössa
   Concatenate CONC to previous line Gedcomin rivin maksimipituus on 255 joten ei tätä aina voi tehdä - kannattaako tehdä koskaan?
Group: 1.2
      Delete orphan records Consolidate multiple identical records - mahdollista mutta työlästä - onko näitä usein?
Group: 2.1
   Delete line blocks ending with ...:
     "1 NOTE" tässä tarkoitetaan yksittäisiä tyhjiä NOTEja, joilla ei ole jatkorivejä (CONC/CONT)
   Delete line block with text check ...:
     "1 EVEN" tarkoitetaan ehkä tyhjää EVEN-rakennetta?
   Delete lines starting with ...:
     "3 SOUR"
     "2 GIVN"
     "2 SURN"
     "3 REFN"
     "1 STAT"
     "3 NOTE"
   Delete lines ending with ...:
     "1 NOTE" tämä varmaan sama kuin aiemmin (tyhjä NOTE)?
Group: 2.2
   Delete empty CONC/CONT lines tyhjiä CONT-rivejä ei voi poistaa - ne merkitsevät tyhjää riviä esim. NOTEn sisällä
   Delete spaces at line end ei saa tehdä ainakaan tägeille NOTE,TEXT,CONT,CONC
   Delete multiple spaces miksi?
   Delete empty DATE + DATE ? lines ok
   Delete multiple identical lines siis peräkkäiset identtiset rivit, paitsi CONT/CONC-rivit
Group: 3.3
   Date BET YYYY AND Y > BET YYYY AND YYYY
   Correct missing year in date range
Group: 5.1 näitä täytyy katsoa tarkemmin sitten kun saan malliksi Sukujutut-gedcomin jossa näitä tilanteita esiintyy
   "Move text":
     "1 NOTE %1#2 SOUR %2" -> "1 NOTE %1"
     "1 ADDR %1" -> "1 ADDR#2 ADR1 %1" eikös alkuperäinen (1 ADDR ...) ole ihan OK?
     "1 EVEN#2 TYPE Ei_julkaista#2 PLAC %1" -> "1 EVEN#2 TYPE Ei_julkaista#2 NOTE %1"
     "1 EMIG" -> "1 RESI"
     "1 EVEN#2 TYPE Kummit#2 PLAC %1" -> "1 EVEN#2 TYPE Kummit#2 NOTE Description: %1"
     "1 EVEN#2 TYPE Tutkijan omat#2 PLAC %1" -> "1 EVEN#2 TYPE Tutkijan omat#2 NOTE %1"
     "1 EVEN#2 TYPE Kolmonen" -> "1 NOTE Kolmo
          



















Lisää kommentteja Liisa Ahosen gedcomin perusteella. Lisäsin näihin oman numeroinnin, jotta eri kohtiin voi viitata helpommin:


Group: -
   0: Coding:  original = ANSI -> UTF-8 - pitää siis vaihtaa CHAR-tägi sekä itse datan koodaus
   OK
  
Group: 1.1
   1.1.1 Lines with nbr. and missing tag insert tag "_DUMMY" eikö näitä voi samantien poistaa?
   Ahosen aineistossa ei ole tällaisia, joten ei toteutetttu
  
   1.1.2 Modify lines without nbr. + tag: Concatenate to previous line - parempi lisätä CONT-rivi, koska yleensä johtuu rivinvaihdosta edellisen rivin sisällössa
   Ahosen aineistossa ei ole tällaisia, joten ei toteutetttu

   1.1.3 Concatenate CONC to previous line Gedcomin rivin maksimipituus on 255 joten ei tätä aina voi tehdä - kannattaako tehdä koskaan?
  Ei toteutetttu

Group: 1.2
      1.2.1 Delete orphan records Consolidate multiple identical records - mahdollista mutta työlästä - onko näitä usein?
  Ei toteutetttu

Group: 2.1
   2.1.1 Delete line blocks ending with ...:
     "1 NOTE" tässä tarkoitetaan yksittäisiä tyhjiä NOTEja, joilla ei ole jatkorivejä (CONC/CONT)
   Ahosen aineistossa on useita tämänmuotoisia tyhjiä kommentteja, muunnos poistaa ne:
      1 NOTE
      2 CONT
      2 CONT
  Lisäksi siellä on tällaisia, joita ei tietenkään poisteta
1 NOTE
2 CONC http://www.sukuhistoria.fi/sshy/sivut/jasenille/paikat.php?bid=25230&p
2 CONC num=414

   2.1.2 Delete line block with text check ...:
     "1 EVEN" tarkoitetaan ehkä tyhjää EVEN-rakennetta?
Aineistossa ei nähdäkseni ole tyhjiä EVEN-rakenteita. Sen sijaan siellä on tällaisia. Mitä niille tehdään, muutetaan NOTEiksi?
1 EVEN
2 TYPE Tutkijan omat
2 PLAC 1900-luvulla itsellisissä, renki

1 EVEN
2 TYPE Kummit
2 PLAC Thomas Thomasson ho Maria Mattsdr pig Lisa Jacobsdr

   2.1.2 Delete lines starting with ...:
     "3 SOUR"
     "2 GIVN"
     "2 SURN"
Nämä liittyvät toisiinsa koska aineistossa on seuraavanlaisia:
1 NAME Yrjö Petter/Rissanen/
2 GIVN
3 SOUR Rantosten sukukirja
2 SURN
3 SOUR Rantosten sukukirja
Näissä on siis nähdäkseni talletettuna se lähde, mistä etu- tai sukunimi on saatu, mikä sinänsä voi olla tarpeellinen tieto? Rakenne on kuitenkin Gedcom-standardin vastainen, SOUR pitäisi olla samalla tasolla kuin GIVN tai SURN. Sisään lukiessa Gramps pudottaa SOUR-tiedot pois ja lisäksi tyhjentää etu- ja sukunimen!

Muuttaisiko tämä tällaiseksi vai poistaako kokonaan:
1 NAME Yrjö Petter/Rissanen/
2 SOUR Rantosten sukukirja

   2.1.3 Delete lines starting with ...:
     "3 REFN"
Aineistossa on pari tällaista
1 BURI
2 PLAC Virolahti
3 REFN IX§08§13§
REFN olisi siis viite johonkin ulkopuoliseen resurssiin tms. Mutta sitä ei saa olla PLAC-tägin alla. Muutetaanko NOTE:ksi vai poistetaanko? Itse asiassa NOTE:n alla voi olla REFN, mutta Gramps ei näytä tukevan tällaista, eikä itse asiassa edes NOTEa PLACin alla:
1 BURI
2 PLAC Virolahti
3 NOTE REFN IX§08§13§
4 REFN IX§08§13§

   2.1.4 Delete lines starting with ...:
     "1 STAT"
Aineistossa on pari tällaista
0 @I25782@ INDI
1 SEX F
1 NAME Aina/Niemelä/
...
1 STAT Personal information researched

Tämä on virheellistä Gedcomia. Gramps näkyy muuttavan sen epästandardiksi tapahtumaksi
1 EVEN
2 TYPE STAT
2 NOTE Description: Personal information researched

Poistetaanko siis kuitenkin?

   2.1.5 Delete lines starting with ...:
     "3 NOTE"

Aineistossa on useita tämäntapaisia:
1 BIRT
2 DATE 15 MAY 1871
2 PLAC Joroinen Syväis
3 NOTE tai Sippola. Merkintä rk epäselvä

1 BIRT
2 DATE 19 DEC 1946
2 PLAC Lahti
3 NOTE (junassa)

1 NAME Maria/Yrjönen/
2 SURN
3 NOTE vihkimäilmoituksesta



   Delete lines ending with ...:
     "1 NOTE" tämä varmaan sama kuin aiemmin (tyhjä NOTE)?
Group: 2.2
   Delete empty CONC/CONT lines tyhjiä CONT-rivejä ei voi poistaa - ne merkitsevät tyhjää riviä esim. NOTEn sisällä
   Delete spaces at line end ei saa tehdä ainakaan tägeille NOTE,TEXT,CONT,CONC
   Delete multiple spaces miksi?
   Delete empty DATE + DATE ? lines ok
   Delete multiple identical lines siis peräkkäiset identtiset rivit, paitsi CONT/CONC-rivit
Group: 3.3
   Date BET YYYY AND Y > BET YYYY AND YYYY
   Correct missing year in date range
Group: 5.1 näitä täytyy katsoa tarkemmin sitten kun saan malliksi Sukujutut-gedcomin jossa näitä tilanteita esiintyy
   "Move text":
     "1 NOTE %1#2 SOUR %2" -> "1 NOTE %1"
     "1 ADDR %1" -> "1 ADDR#2 ADR1 %1" eikös alkuperäinen (1 ADDR ...) ole ihan OK?
     "1 EVEN#2 TYPE Ei_julkaista#2 PLAC %1" -> "1 EVEN#2 TYPE Ei_julkaista#2 NOTE %1"
     "1 EMIG" -> "1 RESI"
     "1 EVEN#2 TYPE Kummit#2 PLAC %1" -> "1 EVEN#2 TYPE Kummit#2 NOTE Description: %1"
     "1 EVEN#2 TYPE Tutkijan omat#2 PLAC %1" -> "1 EVEN#2 TYPE Tutkijan omat#2 NOTE %1"
     "1 EVEN#2 TYPE Kolmonen" -> "1 NOTE Kolmo
         


---------- Forwarded message ---------
From: Kari Kujansuu <kari.kujansuu@gmail.com>
Date: ma 2. heinäk. 2018 klo 12.56
Subject: Re: stk-server/gedcom-käsittely - (oli: Terveisiä Ericin väittäjäisistä)
To: Pekka Valta <pekka.valta@kolumbus.fi>
Cc: Timo Nallikari <timo.nallikari@kolumbus.fi>, Juha Mäkeläinen :-) <juha.makelainen0@saunalahti.fi>, Juha Mäkeläinen <juha.makelainen@iki.fi>, Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>


Kommentteja näihin (punaisella):

Group: -
   Coding:  original = ANSI -> UTF-8 - pitää siis vaihtaa CHAR-tägi sekä itse datan koodaus
Group: 1.1
   Lines with nbr. and missing tag insert tag "_DUMMY" eikö näitä voi samantien poistaa?
   Modify lines without nbr. + tag: Concatenate to previous line - parempi lisätä CONT-rivi, koska yleensä johtuu rivinvaihdosta edellisen rivin sisällössa
   Concatenate CONC to previous line Gedcomin rivin maksimipituus on 255 joten ei tätä aina voi tehdä - kannattaako tehdä koskaan?
Group: 1.2
      Delete orphan records Consolidate multiple identical records - mahdollista mutta työlästä - onko näitä usein?
Group: 2.1
   Delete line blocks ending with ...:
     "1 NOTE" tässä tarkoitetaan yksittäisiä tyhjiä NOTEja, joilla ei ole jatkorivejä (CONC/CONT)
   Delete line block with text check ...:
     "1 EVEN" tarkoitetaan ehkä tyhjää EVEN-rakennetta?
   Delete lines starting with ...:
     "3 SOUR"
     "2 GIVN"
     "2 SURN"
     "3 REFN"
     "1 STAT"
     "3 NOTE"
   Delete lines ending with ...:
     "1 NOTE" tämä varmaan sama kuin aiemmin (tyhjä NOTE)?
Group: 2.2
   Delete empty CONC/CONT lines tyhjiä CONT-rivejä ei voi poistaa - ne merkitsevät tyhjää riviä esim. NOTEn sisällä
   Delete spaces at line end ei saa tehdä ainakaan tägeille NOTE,TEXT,CONT,CONC
   Delete multiple spaces miksi?
   Delete empty DATE + DATE ? lines ok
   Delete multiple identical lines siis peräkkäiset identtiset rivit, paitsi CONT/CONC-rivit
Group: 3.3
   Date BET YYYY AND Y > BET YYYY AND YYYY
   Correct missing year in date range
Group: 5.1 näitä täytyy katsoa tarkemmin sitten kun saan malliksi Sukujutut-gedcomin jossa näitä tilanteita esiintyy
   "Move text":
     "1 NOTE %1#2 SOUR %2" -> "1 NOTE %1"
     "1 ADDR %1" -> "1 ADDR#2 ADR1 %1" eikös alkuperäinen (1 ADDR ...) ole ihan OK?
     "1 EVEN#2 TYPE Ei_julkaista#2 PLAC %1" -> "1 EVEN#2 TYPE Ei_julkaista#2 NOTE %1"
     "1 EMIG" -> "1 RESI"
     "1 EVEN#2 TYPE Kummit#2 PLAC %1" -> "1 EVEN#2 TYPE Kummit#2 NOTE Description: %1"
     "1 EVEN#2 TYPE Tutkijan omat#2 PLAC %1" -> "1 EVEN#2 TYPE Tutkijan omat#2 NOTE %1"
     "1 EVEN#2 TYPE Kolmonen" -> "1 NOTE Kolmonen"
     "1 EVEN#2 TYPE Kaksonen" -> "1 NOTE Kaksonen"

Oletteko muuten huomanneet tämän uuden Gedcom-dokumentin: https://www.tamurajones.net/GEDCOM551AnnotatedEdition.xhtml. Siinä on selvennetty Gedcom-määrityksen ongelmakohtia ym. Varsinainen dokumentti löytyy sivun alareunan "links"-kohdan ensimmäisen linkin kautta (seuraavalta sivulta vielä kohta "downloads").

Kari



1. heinäkuuta 2018 klo 0.13 <pekka.valta@kolumbus.fi> kirjoitti:

    Laitan Hesmerin  tarkemman kuvauksen, mutta periaate on esille nostamissasi tapauksissa

     

    Block  tarkoittaa ao. Tag tasoa ja kaikkia sitä seuraavia alemman tagi tason rivejä. Esim. Person alkaa 0 tagitasolla ja häneen liittyvät tietorivit ovat 01-03(?) tasoilla. Person on siten oma block.

     

    Block ending 01 Note  tarkoittaa yksinkertaisesti, että deletoidaan tyhjät lisätietorivit, koska niissä ei ole tagin säksi mitään tietoa. SJ kirjoitti niitä paljon.

     

    2 GIVN on esimerkki siitä, että SJ kirjoittaa sinänsä oikealla tagi tasolla olevan nimenosan rivin, mutta satunnaisiin paikkoihin 1 NAME blockkia. Koska Gramps pärjää pelkällä 1 NAME rivillä, 2 GIVN ja 2 SURN rivit voi poistaa sekottamasta.

     

    Pekka

     

     

    Lähetetty Windows 10 -puhelimesta

     

    Lähettäjä: Kari Kujansuu
    Lähetetty: lauantai 30. kesäkuuta 2018 21.29
    Vastaanottaja: Pekka Valta
    Kopio: Timo Nallikari; Juha Mäkeläinen :-); Juha Mäkeläinen; Jorma Haapasalo
    Aihe: Re: stk-server/gedcom-käsittely - (oli: Terveisiä Ericin väittäjäisistä)

     

    Varmaankin tuo Sukujutut-korjaus on tehtävissä, mutta tarvitaan kyllä tarkempia speksejä. Ainakaan minä en ymmärrä mitä tarkoittaa esim.

     Delete line blocks ending with ...:
         "1 NOTE"

    Mikä on "line block"?

     

    Tai miksei rivi voi alkaa "2 GIVN" jne? Monet muutkaan kohdat ei nyt kolahda. Saisiko konkreettisia esimerkkejä? Vai onko Hesmerin sivuilla nämä muunnokset kuvattu tarkemmin?

     

    Kari

     

    30. kesäkuuta 2018 klo 20.38 <pekka.valta@kolumbus.fi> kirjoitti:

        Olipa hyvä pläjäys, kiitos Kari. Palautetta muilta, please.

        Olisiko mahdollista lisätä kokonaisuuteen uusi muunnos? Muistanette, että olen korjaillut gedcomien rakennevirheitä Dietrich Hesmerin Conversion-ohjelmalla. Virheet ovat pahimmillaan Sukujuttujen gedcomissa, Grampsin sisäänluku on isoissa ongelmissa ja tietoja katoaa. Tein Ahosen Liisalle Conversion-ohjelmalla ajettavan korjauspaketin, joka eliminoi SJ:n virheet. Kun SJ on  luultavasti sukututkijoiden yleisin ohjelma ja kun Hesmerin ajoa ei saada itsepalveluksi oppimiskynnyksen vuoksi, niin saisiko palvelinohjelmaamme testin, onko gedcomin tuottanut SJ ja tarjota SJ-muunnosta, johon olisi koodattu alla olevat säännöt (tärkein on group 2.1. säännöt).

        Pekka

        ********

        The processing for every record will be performed in the following sequence

        Group: -
           Coding:  original = ANSI -> UTF-8
        Group: 1.1
           Lines with nbr. and missing tag insert tag "_DUMMY"
           Modify lines without nbr. + tag: Concatenate to previous line
           Concatenate CONC to previous line
        Group: 1.2
              Delete orphan records Consolidate multiple identical records
        Group: 2.1
           Delete line blocks ending with ...:
             "1 NOTE"
           Delete line block with text check ...:
             "1 EVEN"
           Delete lines starting with ...:
             "3 SOUR"
             "2 GIVN"
             "2 SURN"
             "3 REFN"
             "1 STAT"
             "3 NOTE"
           Delete lines ending with ...:
             "1 NOTE"
        Group: 2.2
           Delete empty CONC/CONT lines
           Delete spaces at line end
           Delete multiple spaces
           Delete empty DATE + DATE ? lines
           Delete multiple identical lines
        Group: 3.3
           Date BET YYYY AND Y > BET YYYY AND YYYY
           Correct missing year in date range
        Group: 5.1
           "Move text":
             "1 NOTE %1#2 SOUR %2" -> "1 NOTE %1"
             "1 ADDR %1" -> "1 ADDR#2 ADR1 %1"
             "1 EVEN#2 TYPE Ei_julkaista#2 PLAC %1" -> "1 EVEN#2 TYPE Ei_julkaista#2 NOTE %1"
             "1 EMIG" -> "1 RESI"
             "1 EVEN#2 TYPE Kummit#2 PLAC %1" -> "1 EVEN#2 TYPE Kummit#2 NOTE Description: %1"
             "1 EVEN#2 TYPE Tutkijan omat#2 PLAC %1" -> "1 EVEN#2 TYPE Tutkijan omat#2 NOTE %1"
             "1 EVEN#2 TYPE Kolmonen" -> "1 NOTE Kolmonen"
             "1 EVEN#2 TYPE Kaksonen" -> "1 NOTE Kaksonen"

        ***********

     

     

     



     
"""     


"""
g = Gedcom(open(fname,"rb")) #,encoding="iso8859-1"))
print(g)
print(dir(g))
d = g.record_dict()
print(d)
print(d.keys())

#for line in g.line_list():
#    print(line)

for key,value in d.items():
    print(value)
    print(dir(value))
    for line in value.children_tag_records():
        print(line)
#    for line in value.children_lines():
#        print(line)
    break
"""
LINESEP = "\r\n"
LINESEP = "\n"
input_encoding="ISO8859-1"
input_encoding="UTF-8"
output_encoding="UTF-8"


def write(out,s):
    out.write(s)
    #out.write(s.encode(output_encoding))
    
def print_lines(lines):
    for line in lines: print(line)
        
class Gedcom: 
    def __init__(self,items):
        self.items = items
    def print_items(self,out):
        for item in self.items:
            item.print_items(out) 
    
class Item:
    def __init__(self,line,children=None):
        if children is None: children = []
        temp = line.split(None,2)
        self.level= int(temp[0])
        if len(temp) == 1: # 1.1.1
            self.tag = "_DUMMY"
            line = "%s %s" % (self.level,self.tag)
        else:
            self.tag = temp[1]
        self.line = line
        i = line.find(" " + self.tag + " ")
        if i > 0:
            self.text = line[i+len(self.tag)+2:] # preserves leading and trailing spaces
        else:
            self.text = ""
        self.children = children
        while 0 and options.concatenate_lines and len(children) > 0 and children[0].tag in ('CONT','CONC'):
            c = children[0]
            if c.tag == 'CONT':
                x = "\n"
            else:
                x = ""
            x += c.text
            self.text += x
            self.line += x
            del children[0]
            
    def __repr__(self):
        return self.line #+"."+repr(self.children)
    def print_items(self,out):
        #if options.remove_empty_notes and self.tag == "NOTE" and self.children == [] and self.text.strip() == "": return  # drop empty note
        prefix = "%s %s " % (self.level,self.tag)
        if self.text == "":
            write(out,self.line+LINESEP)
        else:
            for line in self.text.splitlines():
                write(out,prefix+line+LINESEP)
                prefix = "%s CONT " % (self.level+1)
        for item in self.children:
            item.print_items(out)

def parse1(lines,level,options):
    linenums = [] # list of line numbers having the specified level 
    prevlevel = -1
    for i,line in enumerate(lines):
        #line = line.strip()
        tkns = line.split(None,1)
        
        if not tkns[0].isdigit(): # 1.1.2
            # assume this is a continuation line
            line = "%s CONT %s" % (prevlevel+1,line)
            tkns = line.split(None,1)
            lines[i] = line
        
        if int(tkns[0]) == level:
            linenums.append(i)
        prevlevel = int(tkns[0])
    
    items = []
    #if len(linenums) == 0: return []
    for i,j in zip(linenums,linenums[1:]+[None]):
        # i and j are line numbers of lines having specified level so that all lines in between have higher line numbers;
        # i.e. they form a substructure
        firstline = lines[i] #.strip()
        item = Item(firstline,parse1(lines[i:j],level+1,options))
        newitem = transform(item,options)
        if newitem == True: # no change
            items.append(item)
            continue
        item = newitem
        if options.display_changes:
            print("-----------------------")
            if item is None: 
                print("Deleted:")
                print_lines(lines[i:j])
            else:
                print("Replaced:")
                print_lines(lines[i:j])
                print("With:")
                if type(item) == list:
                    for it in item:
                        it.print_items(sys.stdout)
                else:
                    item.print_items(sys.stdout)
            print()
            
        if item is None: continue # deleted
        if type(item) == list:
            for it in item:
                items.append(it)
        else:
            items.append(item)
        
    return items

def parse_gedcom(f):
    g = Gedcom([])
    lines = [line[:-1] for line in f.readlines()]
    g.items = parse1(lines,level=0)
    return g

def parse_gedcom_from_file(gedcom_fname,encoding="UTF-8"):
    return parse_gedcom(open(gedcom_fname,encoding=encoding))

def allempty(items):
    for item in items:
        if item.tag not in ('CONT','CONC') or item.text.strip() != "": return False
    return True

def remove_multiple_blanks(text):
    return " ".join(text.split())

def transform(item,options):
    """
    Performs a transformation for the given Gedcom "item" (i.e. "line block")
    Returns one of
    - None: remove the item
    - item: use this item as a replacement (can be the same as input)
    - list of items ([item1,item2,...]): replace the original item with these
    """
    if options.remove_invalid_marriage_dates:
        if item.line.strip() == "1 MARR":
            # replace
            #     1 MARR
            #     2 DATE AVOLIITTO
            # with
            #     1 MARR
            #     2 TYPE AVOLIITTO
            if len(item.children) > 0 and item.children[0].line.startswith("2 DATE AVOLIITTO"):
                item.children[0] = Item("2 TYPE AVOLIITTO")
                return item
            return True # no change

    if options.remove_invalid_divorce_dates:
        if item.line.strip() == "1 DIV":
            # replace
            #     1 DIV
            #     2 DATE .
            # with
            #     1 DIV Y
            if len(item.children) == 1 and item.children[0].line.startswith("2 DATE ."):
                return Item("1 DIV Y")  # this is not valid GEDCOM but Gramps will fix it
            return item

    if options.remove_empty_nameparts: # 2.1.3
        if item.line.strip() in ("2 GIVN","2 SURN"):
            # replace
            #     2 GIVN
            #     3 SOUR xxx
            # with
            #     2 SOUR xxx
            # (same with NOTE instead of SOUR)
            if len(item.children) == 0: return None
            if len(item.children) == 1 and item.children[0].tag in ('SOUR','NOTE'):
                sourline = item.children[0].line
                return Item("2" + sourline[1:])
            return None # empty GIVN/SURN and no subordinate lines => delete
        
    if options.remove_duplicate_sources: # 2.1.3
        if item.line.startswith("1 NAME"):
            prevline = ""
            newchildren = []
            changed = False
            for c in item.children:
                if c.line.startswith("2 SOUR") and c.line == prevline:
                    changed = True
                else:
                    newchildren.append(c)
                prevline = c.line
            item.children = newchildren
            if changed:
                return item
            else:
                return True # no change

    if options.insert_dummy_tags:
        if item.tag == "_DUMMY" and len(item.children) == 0: return None

    if options.remove_empty_notes: # 2.1.1
        if item.tag == "NOTE" and item.text.strip() == "" and allempty(item.children): return None

    if options.remove_empty_dates: # 2.2.4
        if item.tag == "DATE" and item.text.strip() in ('','.','?'): return None

    if options.remove_refn: # 2.1.4
        if item.tag == "REFN": return None

    if options.remove_stat: # 2.1.5
        if item.tag == "STAT": return None

    if options.save_level_3_notes: # 2.1.6
        if item.level == 2 and item.tag == 'PLAC' and len(item.children) == 1 and item.children[0].tag == "NOTE":
            # move NOTE from level 3 to level 2 (including possible CONT/CONC lines)
            # 2 PLAC %1#3 NOTE %2 => 2 PLAC %1#2 NOTE %2
            item2 = Item("2 NOTE %s" % item.children[0].text)
            for c in item.children[0].children:
                c.level -= 1
                c.line = "%s %s %s" % (c.level,c.tag,c.text)
                item2.children.append(c)
            item.children = []
            return [item,item2]

    if options.fix_addr: # 5.1.2
        if item.tag == "ADDR" and item.text.strip() != "":
            for c in item.children:
                if c.tag == "ADR1":
                    return True # no change, ADR1 already exists
            item.children.insert(0,Item("2 ADR1 " + item.text))
            item.text = ""
            item.line = "1 ADDR"
            return item

    if options.fix_events: # 5.1.4
        if (item.tag == "EVEN" and len(item.children) == 2):
            c1 = item.children[0]
            c2 = item.children[1]
            if c1.tag == "TYPE" and c1.text in ('Ei_julkaista','Kummit','Tutkijan omat') and c2.tag == 'PLAC':
                c2.tag = "NOTE"
                if c1.text == "Kummit": c2.text = "Description: " + c2.text
                c2.line = "%s %s %s" % (c2.level,c2.tag,c2.text)
                return item

    if options.fix_events_kaksonen: # 5.1.5
        if (item.tag == "EVEN" and len(item.children) == 1):
            c1 = item.children[0]
            if c1.tag == "TYPE" and c1.text in ('Kaksonen','Kolmonen'):
                c1.tag = "NOTE"
                c1.line = "%s %s %s" % (c1.level,c1.tag,c1.text)
                return item

    if options.remove_multiple_blanks: # 2.2.3
        if item.tag in ('NAME','PLAC'):
            newtext = remove_multiple_blanks(item.text)
            if newtext != item.text:
                item.text = newtext
                item.line = "%s %s %s" % (item.level,item.tag,item.text)
                return item

    return True # no change
    
    
if __name__ == "__main__":
    fname = sys.argv[1]
    g = parse_gedcom_from_file(fname,encoding=input_encoding)
    #out = open("liisa","wb")
    #g.print_items(out)
    g.print_items(sys.stdout)



def add_args(parser):
    #parser.add_argument('--concatenate_lines', action='store_true',
    #                    help='Combine all CONT and CONC lines')
	parser.add_argument('--remove_empty_dates', action='store_true',
						help='Remove invalid DATE tags')
	parser.add_argument('--remove_empty_notes', action='store_true',
						help='Remove empty NOTE tags')
	parser.add_argument('--remove_invalid_marriage_dates', action='store_true',
						help='Remove DATE AVOLIITTO tags')
	parser.add_argument('--remove_invalid_divorce_dates', action='store_true',
						help='Remove invalid DATEs for DIV tags')
	parser.add_argument('--insert_dummy_tags', action='store_true',
						help='Insert s _DUMMY tag if a tag is missing')
	parser.add_argument('--remove_empty_nameparts', action='store_true',
						help='Remove empty GIVN and SURN tags')
	parser.add_argument('--remove_duplicate_sources', action='store_true',
						help='Remove duplicate SOUR lines under NAME')
	parser.add_argument('--remove_refn', action='store_true',
						help='Remove REFN tags')
	parser.add_argument('--remove_stat', action='store_true',
						help='Remove STAT tags')
	parser.add_argument('--save_level_3_notes', action='store_true',
						help='Move level 3 NOTEs to level 2 to save them')
	parser.add_argument('--remove_invalid_dates', action='store_true',
						help='Remove invalid DATEs')
	parser.add_argument('--fix_addr', action='store_true',
						help='Insert ADR1 tags under ADDR')
	parser.add_argument('--fix_events', action='store_true',
						help='Change PLAC tags to NOTEs under certain events')
	parser.add_argument('--fix_events_kaksonen', action='store_true',
						help='Change event types "Kaksonen" and "Kolmonen" to NOTEs')
	parser.add_argument('--remove_multiple_blanks', action='store_true',
						help='Remove _multiple consecutive spaces in person and place names')
	 
def initialize(run_args):
    pass

lines = []
def phase1(run_args, gedline):
    lines.append(gedline.line)
        
def phase2(run_args):
    g = Gedcom([])
    class Options: pass
    options = Options()
    options.__dict__= run_args
    g.items = parse1(lines,level=0,options=options)
    return g
        
