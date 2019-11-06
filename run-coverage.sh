# from: Kari 26.3.2019
# Olen edelleen yrittänyt tehdä sovellukseen (gedcom-osuuteen)
# automaattisia testejä käyttäen "pytest"-työkalua. Lisäksi
# olen kokeillut "coverage"-työkalua, joka osaa kertoa koodirivin
# tarkkuudella, mitä osia sovelluksesta oikeasti on ajettu. Ts. sen
# avulla voi varmistaa että testataan todella sovelluksen kaikkea
# koodia. Coverage osaa generoida paitsi tekstimuotoisen raportin, niin
# myös HTML-sivun jokaisesta sovelluksen Python-modulista, missä se
# näyttää punaisella värillä ne rivit joita ei ole ajettu. Tämä
# tuntuu varsin käyttökelpoiselta ja hauskalta kun yrittää saada
# tuloksen mahdollisimman lähelle sataa prosenttia!
# 
# Käyttämäni testiskripti on test_gedcom.py ja coverage-ajo
# tehdään shell-skriptilla run-coverage.sh. Tuloksena on raportti
# ruudulle sekä em. HTML-tiedostot hakemistoon "htmlcov". Nämä
# ovat sovelluksen juurihakemistossa. Testi käyttää hakemistossa
# "testdata" olevia gedcom-tiedostoja. Coverage pitää ensin asentaa
# (virtuaaliympäristöön) komennolla "pip install coverage".
#
# from: JMä 6.11.2019:
# PyTest asennetaan komennolla "pip install pytest".

coverage run --source app/bp/gedcom -m pytest -vv  -k test_gedcom
coverage report

#coverage run --source app/bp/start -m pytest -vv -k test_start  
#coverage report

coverage html 
