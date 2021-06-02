#   Isotammi Genealogical Service for combining multiple researchers' results.
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
Created on Aug 26, 2020

@author: kari
'''
from bl.gramps.gramps_loader import get_upload_folder
import os
import subprocess
from collections import defaultdict

test_output = """
env;unset PYTHONPATH;rm -r ~/'Sibelius 20200401.gpkg.media';/usr/bin/gramps -i '/home/kari/Documents/eclipse-workspace/stk-upload/uploads/kku/Sibelius 20200401.gpkg' -a tool -p name=verify
W: Disconnected individual, Person: I1146, Falck, Ulrica Charlotta
W: Disconnected individual, Person: I1557, Nikander, Ludvig
W: Old age but no death, Person: I1482, Hämäläinen, Maria Josephsdr.
W: Old age but no death, Person: I2206, Brander, Kaarlo Alfred
W: Disconnected individual, Person: I0132, Peitzius, Margareta
W: Disconnected individual, Person: I0445, Wallenius, August Wilhelm
W: Old age but no death, Person: I2177, Schrey, Otto Volmar
W: Disconnected individual, Person: I0405, Korsu, Beata Johansdotter
W: Disconnected individual, Person: I0425, Sucksdorff, Elias
W: Old age but no death, Person: I2229, Bergholm, Johan
W: Old age but no death, Person: I0536, Arrhenius, Carl Jacob
W: Old age but no death, Person: I0532, Sibelius, Gustaf Hjalmar
W: Old age but no death, Person: I2784, , Anna Ulrica Ulriksdotter
W: Old age but no death, Person: I0927, Torckill, Friederica
W: Disconnected individual, Person: I0435, Sucksdorff, Johan
W: Old age but no death, Person: I0873, Tesche, Catharina Wilhelmina
W: Old age but no death, Person: I1319, Linderoos, Viktor Emil
W: Old age but no death, Person: I1373, , Anna Johansdotter
W: Old age but no death, Person: I1465, Närjänen, Eva Thomasdr.
W: Old age but no death, Person: I1917, Martila, Mårten Johansson
W: Disconnected individual, Person: I2117, Geitel, Natalia
W: Old age but no death, Person: I2208, Brander, Ilmari
W: Disconnected individual, Person: I0043, , Ernest Gustafsson
W: Disconnected individual, Person: I0431, Sucksdorff, Christina
W: Disconnected individual, Person: I1886, Forstén, Fredrika
W: Old age but no death, Person: I0511, Unonius, Anna Elisabeth
W: Old age but no death, Person: I0897, Wegener, Susanna Catharina
W: Old age but no death, Person: I1288, , Mats Jakobsson
W: Disconnected individual, Person: I1548, Wallenius, Henrik Severin
W: Disconnected individual, Person: I1577, Hannula, T W
W: Old age but no death, Person: I2178, Schrey, Sophia Amalia
W: Old age but no death, Person: I2186, Stårck, Nicolaus
W: Old age but no death, Person: I0464, Sucksdorff, Ulrica Elisabet
W: Disconnected individual, Person: I0464, Sucksdorff, Ulrica Elisabet
W: Old age but no death, Person: I0693, Broman, Abraham
W: Old age but no death, Person: I0923, Torckill, barn
W: Unknown gender, Person: I0923, Torckill, barn
W: Old age but no death, Person: I2152, Swan, Salome
W: Old age but no death, Person: I0544, Sucksdorff, Christoffer Isak Vilhelm
W: Old age but no death, Person: I0146, Åkerberg, Elias Ulric
W: Disconnected individual, Person: I0353, Norring, Hans
W: Old age but no death, Person: I1848, Hägerflygt, Magdalena Friederica
W: Disconnected individual, Person: I0399, , Walborg Andersdotter
W: Disconnected individual, Person: I0439, Arrhenius, N
W: Old age but no death, Person: I0521, , Maria Andersdotter
W: Old age but no death, Person: I1784, , Jacob Jacobsson
W: Disconnected individual, Person: I0193, Wegelius, Berndt Wilhelm
W: Old age but no death, Person: I0285, Malm, Hedvig
W: Disconnected individual, Person: I1532, Selin, Erik Richard (Salo)
W: Old age but no death, Person: I1706, Gottleben, Catharina Gabriesdotter
W: Old age but no death, Person: I1470, Puttro, Anna Josephsdr.
W: Disconnected individual, Person: I1595, Hilden, Johan Evert
W: Old age but no death, Person: I1814, Salén, Amanda Anastasia Constantia
W: Disconnected individual, Person: I0446, Odenvall, Fredric Julius
W: Old age but no death, Person: I1439, Puttro, Maria Davidsdotter
W: Disconnected individual, Person: I1444, Hämäläin, Moses Johansson
W: Disconnected individual, Person: I1519, Forsström, Evert Jonathan
W: Disconnected individual, Person: I1563, Forssman, Carl Johan Jacob
W: Old age but no death, Person: I0864, Kuhlman, Sophia Dorothea
W: Disconnected individual, Person: I1578, Nyman, Alfred
W: Old age but no death, Person: I0034, Utter, Otto Gustaf
W: Disconnected individual, Person: I0400, , Johan Mattsson
W: Old age but no death, Person: I0669, Kuhlberg, Johan Fredrich
W: Old age but no death, Person: I1650, Sevon, Martha Emilia
W: Old age but no death, Person: I1884, Sommers, Ulrica Scharlotta
W: Old age but no death, Person: I0541, Åkerberg, Christina Gustava
W: Disconnected individual, Person: I1538, Nylund, Johan Alfred
W: Disconnected individual, Person: I1581, Hilden, Emanuel Lennart
W: Disconnected individual, Person: I0381, Flor, Johanna
W: Old age but no death, Person: I1053, von Borgen, Christina
W: Old age but no death, Person: I1497, Putro, Johan Andersson
W: Disconnected individual, Person: I1530, Laurinus, Theodor Theosofius
W: Disconnected individual, Person: I0385, Hedman, Jacob Johan
W: Disconnected individual, Person: I0423, Linderoos, N
W: Old age but no death, Person: I2170, Linbom, Gustaf Adolf
W: Disconnected individual, Person: I0139, Unonius, N
W: Old age but no death, Person: I0207, Järnefelt, Olof Anders
W: Old age at death, Person: I1969, Flink, Maria Gustafsdotter
W: Old age but no death, Person: I1468, Tikka, Maria Petri
W: Disconnected individual, Person: I1546, Liljelund, Axel Johan Hjalmar
W: Old age at death, Person: I0036, Clodt von Jürgensburg, Elisabeth
W: Disconnected individual, Person: I0379, Gyldenär, Beata
W: Disconnected individual, Person: I1567, Sohlman, Karl Oskar
W: Disconnected individual, Person: I0064, Hyttinen, Paulus
W: Old age but no death, Person: I1946, Rautell, Eric Ehrsson
W: Old age but no death, Person: I17418, Unonius, Petter Mårten Eliasson
W: Disconnected individual, Person: I0409, Thesche, N
W: Old age but no death, Person: I0529, , Henrik Johansson
W: Disconnected individual, Person: I1542, Hartwall, Bernhard Adolf
W: Old age but no death, Person: I2230, , Maria Gabrielsdotter
W: Old age but no death, Person: I0347, Åkerberg, Gustava
W: Disconnected individual, Person: I0466, Lundmark, N
W: Disconnected individual, Person: I0402, Kiljander, Petter Johan
W: Old age but no death, Person: I1486, Hellsten, Reseda Theresia
W: Old age but no death, Person: I1918, , Hedvig Andersdotter
W: Old age but no death, Person: I2179, Schrey, Carl Johan
W: Disconnected individual, Person: I0382, Bruncrona, Abraham Mathias
W: Old age but no death, Person: I2577, , Gustafva Eleonora Abrahamsdotter
W: Old age but no death, Person: I2185, Stårck, Fredrik Henrik
W: Disconnected individual, Person: I0398, Saarela, Daniel Johansson
W: Disconnected individual, Person: I0427, Unonius, N. W.
W: Old age but no death, Person: I1211, Granit, Fanny Nathalia
W: Disconnected individual, Person: I2193, , Simon Simonsson
W: Old age but no death, Person: I0877, Tesche, Anna Benedicta
W: Disconnected individual, Person: I1950, Pulchinen, Catharina
W: Disconnected individual, Person: I2010, Wahlros, Erika
W: Disconnected individual, Person: I0360, Wallgreen, Jungfru
W: Old age but no death, Person: I1648, Ingberg, Emilia Johanna
W: Old age but no death, Person: I1985, Warenberg, Carl Anton
W: Old age but no death, Person: I2191, Zimmerman, Margareta
W: Disconnected individual, Person: I2191, Zimmerman, Margareta
W: Old age but no death, Person: I0828, Qvist, Carl Johan
W: Old age but no death, Person: I0915, Torckill, Carl
W: Old age but no death, Person: I1067, Stenberg, David Simonsson
W: Disconnected individual, Person: I0424, Linderoos, N
W: Disconnected individual, Person: I1527, Liljelund, Karl Sigurd Oskar
W: Disconnected individual, Person: I1852, Gripenvald, N
W: Old age but no death, Person: I0825, Ignatius, Bengt
W: Old age but no death, Person: I1351, , Erik Nilsson
W: Old age but no death, Person: I2242, Geitel, Wladimir Fredik Alexander
W: Disconnected individual, Person: I0430, Sucksdorff, C. G.
W: Old age but no death, Person: I1550, Stolpe, Torfinn
W: Disconnected individual, Person: I1550, Stolpe, Torfinn
W: Disconnected individual, Person: I0007, Borg, Aaron Gustav
W: Old age but no death, Person: I1293, , Anna Johansdotter
W: Old age but no death, Person: I0550, Björckstén, Johan Isaak
W: Disconnected individual, Person: I0438, Hougberg, N
W: Old age but no death, Person: I1960, Flink, Hanna Hilja Maria
W: Old age but no death, Person: I1635, Åberg, Elisabet Sophia
W: Disconnected individual, Person: I1885, Brusin, N
W: Old age but no death, Person: I0537, Sucksdorff, Elisabet
W: Disconnected individual, Person: I0369, Holm, Anna Chatarina
W: Disconnected individual, Person: I0452, Heldt, Johan Fredric
W: Old age but no death, Person: I0548, Sucksdorff, Fredrik Emil
W: Old age but no death, Person: I0673, Kuhlberg, Fredrich Israel
W: Old age but no death, Person: I1415, Grundström, Axel Johan
W: Disconnected individual, Person: I1524, Juvelius, Walter Henrik
W: Old age but no death, Person: I1625, Swan, Lyyli
W: Disconnected individual, Person: I1625, Swan, Lyyli
W: Disconnected individual, Person: I0053, Lilius, Henric
W: Old age but no death, Person: I0907, Wäger, Johannes
W: Old age but no death, Person: I1989, Sjöstedt, Elin
W: Old age but no death, Person: I1496, Puttro, Maria Adamsdr.
W: Old age but no death, Person: I1515, Putro, Inkeri Maria
W: Old age but no death, Person: I0851, Tesche, Margaretha Hedwig
W: Old age but no death, Person: I0924, Torckill, Wilhelmina
W: Old age but no death, Person: I0984, Bruun, Johannes
W: Disconnected individual, Person: I0363, von Tigerström, N
W: Disconnected individual, Person: I0195, Borg, Julia
W: Old age but no death, Person: I1453, Närjänen, Moses Henriksson
W: Old age but no death, Person: I1479, Hämäläinen, Josef Josefsson
W: Old age but no death, Person: I0542, Sucksdorff, Adolf Mathias Israel
W: Disconnected individual, Person: I1573, Nikander, Karl Adolf (Niinisalo)
W: Old age but no death, Person: I0545, Sucksdorff, Christina Gustava
W: Old age at death, Person: I1359, Hellenius, Maria Christina
W: Old age but no death, Person: I1849, Posse, Fredrik
W: Disconnected individual, Person: I1849, Posse, Fredrik
W: Old age but no death, Person: I0040, Helenius, Josefina Antintytär
W: Disconnected individual, Person: I0040, Helenius, Josefina Antintytär
W: Disconnected individual, Person: I0359, Wallgreen, Fru
W: Old age but no death, Person: I0510, , Hilda Mathilda Henriksson
W: Old age but no death, Person: I1317, Linderoos, Johan Adolf
W: Old age but no death, Person: I1516, Putro, Veikko Juso Matti
W: Old age but no death, Person: I0090, Tesche, Maria Charlotta
W: Disconnected individual, Person: I1134, Steinheil, Fabian
W: Disconnected individual, Person: I1534, Lindvall, Karl Georg
W: Old age but no death, Person: I0540, Sucksdorff, Israel
W: Old age but no death, Person: I1013, Anderseen, Maria
W: Old age but no death, Person: I1783, , Henric Johansson
W: Old age but no death, Person: I1975, Flink, Gustaf Adolph
W: Disconnected individual, Person: I1508, Putro, Anna Christersdr.
W: Old age but no death, Person: I1493, Hirvonen, Adam Stephansson
W: Disconnected individual, Person: I1588, Koskinen, Juha Heikki (Digert)
W: Old age but no death, Person: I1461, Puttro, Walborg Abrahamsdr.
W: Old age but no death, Person: I0328, Göhle, Brita Elisabetha
W: Disconnected individual, Person: I1575, Moren, Paavo Emil Garibaldi
W: Old age but no death, Person: I0049, , Annikka Mattsdotter
W: Disconnected individual, Person: I0392, Hedenberg, Margareta
W: Old age but no death, Person: I1745, Johansson, Gustaf
W: Old age but no death, Person: I0346, Åkerberg, Johanna Fredrica
W: Old age but no death, Person: I0586, Borg, Anders Johan
W: Old age but no death, Person: I0670, Kuhlberg, Henric Leonard
W: Old age but no death, Person: I0829, Qvist, Anna Margaretha
W: Old age but no death, Person: I1568, Wegelius, Karl Albert
W: Disconnected individual, Person: I1568, Wegelius, Karl Albert
W: Disconnected individual, Person: I2116, Eriksson, Ebba
W: Old age but no death, Person: I0517, Unonius, Laurentius (Lars)
W: Disconnected individual, Person: I0142, Unonius, Anna Lisa
W: Old age but no death, Person: I0941, Sundblad, Dorothea Elisabeth
W: Old age but no death, Person: I0350, Göhle, Wendla Carolina
W: Disconnected individual, Person: I0143, Östberg, Karl
W: Disconnected individual, Person: I0384, Forselius, Gabriel
W: Old age but no death, Person: I0516, , Gustaf Johansson
W: Old age but no death, Person: I1492, Hirvonen, Anna Stephansdr.
W: Disconnected individual, Person: I1587, Ingman, Johan Albinus
W: Old age but no death, Person: I1495, Putro, Eva Henrichsdr.
W: Old age but no death, Person: I1458, Närjänen Hiest, Maria Thomasdr.
W: Disconnected individual, Person: I0429, Unonius, M. L.
W: Disconnected individual, Person: I1574, Lindroos, Karl (Töyry)
W: Old age but no death, Person: I2149, Swan, Susanna Charlotta
W: Old age but no death, Person: I2189, , Anna Gabrielsdotter
W: Old age but no death, Person: I2190, Wång, Alexander Magnus
W: Disconnected individual, Person: I2190, Wång, Alexander Magnus
W: Disconnected individual, Person: I1551, Hällström, Johan Erik
W: Old age but no death, Person: I1476, Kapanen, Sophia Adamsdr.
W: Old age but no death, Person: I1514, Putro, Maria
W: Disconnected individual, Person: I1520, Murén, Aksel Walfrid
W: Old age but no death, Person: I1767, Sommers, Uolevi Kaarle Johannes
W: Disconnected individual, Person: I0449, Sohlberg, Herman Fredric
W: Disconnected individual, Person: I0436, Sucksdorff, Joachim
W: Old age but no death, Person: I1195, Mörtengren, Magdalena Sophia
W: Old age but no death, Person: I2068, Trygg, Maria Lovisa
W: Disconnected individual, Person: I2125, Ilmonen, Mathilda
W: Old age but no death, Person: I2239, , Matts Henriksson
W: Disconnected individual, Person: I2114, Sommer, Eva
W: Old age but no death, Person: I1459, Jäskeläinen, Anna Johansdr.
W: Disconnected individual, Person: I1529, Schulman, Ossian Karl Leonard
W: Old age but no death, Person: I2151, Swan, Hanna
W: Disconnected individual, Person: I0196, Wegelius, Henriette
W: Disconnected individual, Person: I0450, Ejmeleus, Nils A.
W: Old age but no death, Person: I0587, Borg, Friedrich Adolph
W: Old age at death, Person: I1243, Sundman, Johanna Elisabeth
W: Disconnected individual, Person: I0280, Tesche, N
W: Old age but no death, Person: I2956, , Anna Simonsdotter
W: Old age but no death, Person: I4879, Stenberg, Erland Simonsson
W: Old age but no death, Person: I2203, Väisänen, Maria Katharina
W: Disconnected individual, Person: I0094, Sineclair, Caroline
W: Old age but no death, Person: I1425, Juvonen, Nanna Sofia
W: Old age but no death, Person: I0546, Sucksdorff, Christian Gustav
W: Disconnected individual, Person: I0378, Mennander, Johan
W: Old age but no death, Person: I1270, Molin, Sofia
W: Old age but no death, Person: I1443, Puttro, Maria Davidsdotter
W: Old age but no death, Person: I1477, Putro, Maria Henriksdr.
W: Old age but no death, Person: I1942, , Eric Adamsson
W: Old age but no death, Person: I0519, , Maria Henriksdotter
W: Old age but no death, Person: I2957, , Andreas Simonsson
W: Old age but no death, Person: I0806, Heidenstrauch, Lars Petter
W: Old age but no death, Person: I1837, Stråhlman, Hedvig Sophia
W: Disconnected individual, Person: I1951, Lamppu, Adam
W: Disconnected individual, Person: I1330, Alopeus, Magnus
W: Old age but no death, Person: I1528, Tötterman, Evert Wilhelm
W: Disconnected individual, Person: I1528, Tötterman, Evert Wilhelm
W: Old age but no death, Person: I0488, Unonius, Johannes (Jean)
W: Old age but no death, Person: I0553, Björckstén, Ida
W: Old age but no death, Person: I1419, Kaipiainen, Maria Mosesdotter
W: Disconnected individual, Person: I2124, Lehtonen, David
W: Old age at death, Person: I0826, Elfwengren, Anna
W: Old age but no death, Person: I1920, , Maria Michelsdotter
W: Old age but no death, Person: I2099, Harlin, Regina
W: Old age but no death, Person: I2180, Parlin, Thomas Thomasson
W: Old age but no death, Person: I0041, , Maria Johanna Mariantytär
W: Disconnected individual, Person: I0041, , Maria Johanna Mariantytär
W: Old age but no death, Person: I2196, , Maria Johansdotter
W: Old age but no death, Person: I0522, , Maria Gustafsdotter
W: Old age but no death, Person: I0728, , Matthias Mattsson
W: Old age but no death, Person: I1122, von Briskorn, Friedrich Wilhelm
W: Old age but no death, Person: I1713, Sommers, Maria Anna Theodora
W: Disconnected individual, Person: I1140, Suchsdorff, Christopher
W: Old age but no death, Person: I1895, Glad, Alexandra Wilhelmina
W: Old age but no death, Person: I2083, Becker, Gabriel Wilhelm Julian
W: Old age but no death, Person: I0920, Torckill, dotter
W: Old age but no death, Person: I0928, Torckill, Carolina
W: Disconnected individual, Person: I1448, , Adam Andersson
W: Old age but no death, Person: I2085, Becker, Adolphina Leonora
W: Disconnected individual, Person: I0963, Torckill, Anna
W: Old age but no death, Person: I1315, Linderoos, Gustaf Mathias Israel
W: Old age but no death, Person: I2130, Nyberg, Claës Henrik
W: Old age but no death, Person: I3901, , Sophia Johansdotter
W: Old age but no death, Person: I1337, , Maria Lisa Hindersdotter
W: Old age but no death, Person: I0523, , Anna Sophia Gustafsdotter
W: Disconnected individual, Person: I1131, Devier, Peter
W: Disconnected individual, Person: I1132, Sprengtporten, Göran Magnus
W: Disconnected individual, Person: I1591, Ahlgren, Johan Emil Eberhard
W: Old age but no death, Person: I2796, , Johan Henricsson
W: Old age but no death, Person: I1145, Dahlman, Sara Abrahamsdotter
W: Old age but no death, Person: I1511, Krane?, Anna Maria
W: Old age but no death, Person: I1922, , Anders Michelsson
W: Disconnected individual, Person: I0045, Wanaeus, Johan
W: Old age but no death, Person: I0156, Sundblad, Henric Wilhelm
W: Old age but no death, Person: I1353, Närjänen, Elisabeth Mosesdotter
W: Old age but no death, Person: I1429, Wahlman, Sofia Lovisa
W: Old age but no death, Person: I1851, Stackelberg, Fredrik Ulrik Bernt Otto
W: Disconnected individual, Person: I1851, Stackelberg, Fredrik Ulrik Bernt Otto
W: Disconnected individual, Person: I0377, Floor, Otto
W: Old age but no death, Person: I1372, , Anders Andersson
W: Old age but no death, Person: I1943, , Sophia Ehrsdotter
W: Disconnected individual, Person: I1559, Mäkinen, Henrik August
W: Old age but no death, Person: I0940, Sundblad, Andreas
W: Old age but no death, Person: I1376, , Johan Andersson
W: Old age but no death, Person: I1797, Putronen, Moses
W: Disconnected individual, Person: I1797, Putronen, Moses
W: Old age but no death, Person: I0549, Björksten, Vendla Evelina
W: Old age but no death, Person: I0874, Wickberg, Anna Christina
W: Disconnected individual, Person: I1592, Nyberg, Berndt Edvard
W: Old age but no death, Person: I1871, Björnberg, Anna Beata
W: Unknown gender, Person: I2043, Nettisivusto, Kertova
W: Disconnected individual, Person: I2043, Nettisivusto, Kertova
W: Disconnected individual, Person: I2078, Skutnabb, Teodor
W: Old age but no death, Person: I2219, Flink, Gundel Henriette
W: Old age but no death, Person: I1512, Krane?, Henrika
W: Old age but no death, Person: I2234, Bergholm, Gustava
W: Disconnected individual, Person: I0419, Unonius, Vilhelmina
W: Old age but no death, Person: I1490, Sparre, Anna Petersdr.
W: Old age but no death, Person: I2205, Snellman, Hans Arthur
W: Old age but no death, Person: I2213, Wegelius, Maximilian Henrik
W: Disconnected individual, Person: I0453, Mellin, Lovisa
W: Old age but no death, Person: I0159, Boxberg, Maria Christina
W: Old age but no death, Person: I0798, Heidenstrauch, Claës
W: Old age but no death, Person: I0855, Tesche, Catharina
W: Old age but no death, Person: I1150, Gylling, Carl Fredric
W: Old age but no death, Person: I1628, Svahn, Katharina Elisabeth
W: Old age but no death, Person: I0039, Seppälä, Hedvig Mattsdotter
W: Disconnected individual, Person: I0404, Mustakangas, Gustaf Nilsson
W: Old age but no death, Person: I0604, Wangel, Gustaf Adolf
W: Disconnected individual, Person: I0448, Erlin, Jonas Anton
W: Old age but no death, Person: I0531, Sibelius, Wilhelm
W: Old age but no death, Person: I0792, Ekerodde, Petrus
W: Old age but no death, Person: I1273, Jäderholm, Ida Maria
W: Old age but no death, Person: I1986, Warenberg, Catharina Charlotta
W: Old age but no death, Person: I0208, Carlquist, Helena Katariina
W: Disconnected individual, Person: I0437, Flodberg, Margareta Charlotta
W: Old age but no death, Person: I2218, Flink, Elin Maria Clementine
W: Old age but no death, Person: I1331, , Gustaf Henriksson
W: Disconnected individual, Person: I1877, Tigerstedt, Gustaf Adolf
W: Old age but no death, Person: I2102, Cleve, Zachris Joakim
W: Disconnected individual, Person: I0474, Holmberg, N
W: Old age but no death, Person: I1764, , Anna Jacobsdotter
W: Old age but no death, Person: I0027, Utter, Johanna Juliana
W: Old age but no death, Person: I2958, , Maja Stina Simonsdotter
W: Old age but no death, Person: I1494, Puttro, Justina Josepsdr.
W: Old age but no death, Person: I0116, , Henrik Mattsson
W: Disconnected individual, Person: I0188, Renvall, Carl Gustaf
W: Disconnected individual, Person: I0411, Kyander, Magnus Johan
W: Disconnected individual, Person: I0454, Borg, Carolina Vilhelmina
W: Disconnected individual, Person: I1589, Koskinen, Juho
W: Old age at death, Person: I0591, Swan, Kaino Ihanelma
W: Old age but no death, Person: I3906, , Abraham Johansson
W: Disconnected individual, Person: I1670, Grahn, Ida
W: Old age but no death, Person: I1904, Jägerroos, Jakob Henrik
W: Old age but no death, Person: I0552, Björckstén, Wendla Evelina
W: Old age at death, Person: I0035, Järnefelt, Aino
W: Disconnected individual, Person: I0201, Sandberg, Olivia
W: Old age but no death, Person: I0524, , Anna Sofia Johansdotter
W: Old age but no death, Person: I1292, , Johan Johansson
W: Disconnected individual, Person: I1854, von Gutofsky, Johan Henrik
W: Old age but no death, Person: I0348, Åkerberg, Sophia
W: Disconnected individual, Person: I0410, Scharp, C. A.
W: Old age but no death, Person: I2955, , Ephraim Simonsson
W: Disconnected individual, Person: I1953, Kähönen, Anna
W: Old age but no death, Person: I1316, Linderoos, Carl Wilhelm Julius
W: Old age but no death, Person: I1440, Puttro, Judith Davidsdotter
W: Old age but no death, Person: I1526, Uotila, Elias Werner
W: Disconnected individual, Person: I1526, Uotila, Elias Werner
W: Old age but no death, Person: I1939, , Maria Elisabet Ericsdotter
W: Old age but no death, Person: I1979, Warenberg, Maria Magdalena
W: Old age but no death, Person: I2202, Snellman, Viktor
W: Disconnected individual, Person: I0376, Mennander, J.H.
W: Disconnected individual, Person: I0418, Kyander, Gustava
W: Disconnected individual, Person: I0455, Lohjander, Fredrique
W: Old age but no death, Person: I0776, , Sara Johansdotter
W: Old age but no death, Person: I1037, Sandheim, Christina Elisabeth
W: Old age but no death, Person: I1060, Tuderus, Eva Magdalena
W: Old age but no death, Person: I1302, , Anna Henrichsdotter
W: Old age but no death, Person: I1371, , Hedda Nilsdr.
W: Disconnected individual, Person: I1371, , Hedda Nilsdr.
W: Old age but no death, Person: I8931, , Karl Wilhelm Gustafsson
W: Old age but no death, Person: I1279, , Anna Jakobsdotter
W: Old age but no death, Person: I2150, Swan, Johan Edvard
W: Old age but no death, Person: I0171, Norrgren, Henrietta Maria
W: Disconnected individual, Person: I1445, Kaipiainen, Eva Mosesdotter
W: Old age but no death, Person: I1919, Martila, Johan Mattsson
W: Old age but no death, Person: I0534, Unonius, Juliana Dorothea
W: Old age but no death, Person: I0802, Heidenstrauch, Claës
W: Old age but no death, Person: I1320, Linderoos, Alina Wilhelmina
W: Disconnected individual, Person: I1539, Isopere, Werner Donatius
W: Old age but no death, Person: I2227, , Henrik Reinhold Henriksson
W: Disconnected individual, Person: I0192, Thermán, Anton
W: Old age but no death, Person: I1015, Sipelius, Christina
W: Old age but no death, Person: I1935, Rautell, Susanna
W: Old age but no death, Person: I0543, Sucksdorff, Fredrika Wilhelmina Andrietta
W: Disconnected individual, Person: I0362, Kulg???, Brita
W: Old age at death, Person: I0257, Granit, Amanda Mathilda
W: Disconnected individual, Person: I1553, Kokkonen, Frans Edvard
W: Disconnected individual, Person: I2192, , Johan Gabriel Johansson
W: Disconnected individual, Person: I0403, Junnila, Lisa Henriksdotter
W: Old age but no death, Person: I0576, Utter, Johan
W: Old age but no death, Person: I1280, , Maria Jakobsdotter
W: Disconnected individual, Person: I1678, Smirnov, Anna
W: Disconnected individual, Person: I1164, Sacklén, Niclas Henric
W: Old age but no death, Person: I1624, Slöör, Fredrik Mikael
W: Old age but no death, Person: I2198, Sandman, Jonathann
W: Old age but no death, Person: I0349, Göhle, Anna Fredrica
W: Disconnected individual, Person: I0447, Sevón, Edward
W: Old age but no death, Person: I0672, Kuhlberg, Maria Gustafva
W: Disconnected individual, Person: I1593, Nieminen, Valdemar
W: Old age but no death, Person: I2217, Wegelius, William Esaias
W: Disconnected individual, Person: I1560, Nordensvan, Johan Robert Hugo
W: Disconnected individual, Person: I0393, Fortelius, Gabriel
W: Disconnected individual, Person: I1564, Joselin, Edvin
W: Old age but no death, Person: I0530, , Anna Eriksdotter
W: Old age but no death, Person: I0858, Kuhlman, Hans Didric
W: Old age but no death, Person: I1580, Silander, Gustaf Petter
W: Disconnected individual, Person: I1580, Silander, Gustaf Petter
W: Disconnected individual, Person: I2115, Sommer, Anna
W: Old age but no death, Person: I1121, von Briskorn, Jacob Gottlieb
W: Old age at death, Person: I1313, Åkerberg, Vilhelmina Elisabet
W: Old age but no death, Person: I1505, Kappinen, Johan Adami
W: Old age but no death, Person: I1957, Nyberg, Maria Charlotta
W: Disconnected individual, Person: I0058, Seminoff, N
W: Disconnected individual, Person: I1549, Lindström, Oskar myöh.Lyytinen
W: Disconnected individual, Person: I1566, Sokoloff, Nikolai
W: Old age but no death, Person: I1955, Flink, Henrik Gustaf
W: Old age but no death, Person: I0661, Randelin, Fredrik
W: Old age but no death, Person: I0765, Palenius, Anna Christina
W: Old age but no death, Person: I3905, , Johan Johansson
W: Old age but no death, Person: I1045, Cupræa, Margaretha Jacobsdotter
W: Old age but no death, Person: I1987, Wahrenberg, Gustava Christina
W: Old age but no death, Person: I1994, Wahlroos, Anna Mathilda
W: Disconnected individual, Person: I1133, Barclay de Tolly, Mihail
W: Disconnected individual, Person: I1326, Janisch, Carl
W: Disconnected individual, Person: I0459, Weman, Fredrique
W: Old age but no death, Person: I1070, , Anna Emerentia Davidsdotter
W: Old age but no death, Person: I2215, Wegelius, Johan Eugen
W: Disconnected individual, Person: I0433, Flodberg, Class Magnus
W: Disconnected individual, Person: I0387, Hedenberg, Malachias
W: Old age but no death, Person: I1467, Kyllinen, Lovisa Paulsdr.
W: Disconnected individual, Person: I1584, Kauppinen, Evert
W: Old age but no death, Person: I2121, Mellberg, Edla Johanna
W: Disconnected individual, Person: I0370, Wenandra, Anna Maria
W: Disconnected individual, Person: I0199, Idestam, Maria
W: Old age but no death, Person: I0202, Göhle, Martha Wendla
W: Disconnected individual, Person: I1554, Weseloff, Alexander
W: Old age but no death, Person: I0217, Wadsteen, Maria
W: Old age but no death, Person: I0937, Sundblad, Anna Margareta
W: Old age but no death, Person: I2204, Snellman, Viktor Oskar
W: Old age but no death, Person: I17400, Blåfield, Lovisa Katarina
W: Old age but no death, Person: I0584, Borg, Helena Elisabet
W: Old age but no death, Person: I0674, Kuhlberg, Abraham
W: Old age but no death, Person: I0879, Tesche, Johanna Margaretha Natalia
W: Disconnected individual, Person: I0547, von Willebrand, Märta
W: Disconnected individual, Person: I0066, Korpela, Kaarle
W: Old age but no death, Person: I1937, , Susanna Ericsdotter
W: Disconnected individual, Person: I0344, Härmä, Henrik
W: Disconnected individual, Person: I0367, Forsell, Johanna Ulrica
W: Old age but no death, Person: I5238, , David Bernhard Davidsson
W: Old age but no death, Person: I1003, Tesche, Jacob
W: Old age but no death, Person: I1934, Sandbäck, Johan David
W: Disconnected individual, Person: I1948, Lamppu, Henrik
W: Old age but no death, Person: I2241, Geitel, Alexander Petter
W: Old age but no death, Person: I0526, , Maria Johansdotter
W: Old age but no death, Person: I0588, Borg, Maria Christina
W: Old age but no death, Person: I1488, Mether-Borgström, Ernst Johan
W: Old age but no death, Person: I1810, Morén, Laurenz
W: Disconnected individual, Person: I0190, Björksten, Gustaf Richard
W: Disconnected individual, Person: I0471, Holmsten, Carolina
W: Disconnected individual, Person: I0451, Justin, Gustaf Adolf
W: Disconnected individual, Person: I0364, Röngren, Isaac
W: Disconnected individual, Person: I0394, Junnila, Henrich Danielsson
W: Old age but no death, Person: I2194, Sandman, Ephraim
W: Old age but no death, Person: I2195, Sandman, Jacob Mattson
W: Disconnected individual, Person: I0458, Blåfield, Euphodine
W: Disconnected individual, Person: I2118, Sommer, Enni
W: Old age but no death, Person: I0811, Heidenstrauch, Gabriel
W: Old age but no death, Person: I0028, Gottsman, Margretha Elisabetha
W: Disconnected individual, Person: I1676, Hedberg, Maria
W: Old age but no death, Person: I1961, Flink, Knut Adrian
W: Old age but no death, Person: I2659, , Maria Ulrica Gustavsdotter
W: Old age but no death, Person: I1547, Boisman, Almar Henrik
W: Disconnected individual, Person: I1547, Boisman, Almar Henrik
W: Old age but no death, Person: I2175, Phaler, Fredrika Eleonora
W: Old age but no death, Person: I0172, Norrgren, Johanna Carolina
W: Disconnected individual, Person: I0357, , Catharina Mattsdotter
W: Disconnected individual, Person: I1522, Peltonen, Werner Donatus
W: Disconnected individual, Person: I1579, Lindgren, K E
W: Disconnected individual, Person: I0126, Juslenia, Marg.
W: Disconnected individual, Person: I0390, Gadolin, Hedvig
W: Disconnected individual, Person: I0133, Wanaeus, Catharina
W: Disconnected individual, Person: I0417, Lindroos, Jeanette
W: Disconnected individual, Person: I0442, Hougberg, Carl Adolf Svensson
W: Old age but no death, Person: I0980, Bruun, Margaretha
W: Old age but no death, Person: I1035, Sandheim, Jacob Johan
W: Old age but no death, Person: I1284, , Elisabet Jakobsdotter
W: Old age but no death, Person: I2212, Tallberg, Sofie Wilhelmina
W: Disconnected individual, Person: I1571, Mustila, August
W: Disconnected individual, Person: I1561, Weckman, Karl Gustaf
W: Old age but no death, Person: I1414, Blåfield, Carl Fredric
W: Disconnected individual, Person: I1414, Blåfield, Carl Fredric
W: Old age but no death, Person: I1343, , Hendrik Hansson
W: Old age but no death, Person: I2049, Wegelius, Wilhelm
W: Old age but no death, Person: I1583, Pälsi, August Hjalmar
W: Disconnected individual, Person: I1583, Pälsi, August Hjalmar
W: Old age but no death, Person: I1923, , Christina Henriksdotter
W: Old age but no death, Person: I1018, Alopæus, Magnus Jacobus
W: Old age but no death, Person: I1504, Putro, Catharina Heinrichsdr.
W: Old age but no death, Person: I1632, Winter, Katarina Margareta
W: Old age but no death, Person: I1715, Sommer, Theodor Wilhelm
W: Old age but no death, Person: I0551, Björckstén, Gustaf Richard
W: Disconnected individual, Person: I0198, Björksten, Hilda
W: Old age but no death, Person: I1208, Granit, Gustaf Edward
W: Old age but no death, Person: I2084, Becker, Gustaf Patric Theophile
W: Old age but no death, Person: I17277, Björkman, Johanna Henriksdotter
W: Disconnected individual, Person: I0457, Sevón, Anna
W: Old age but no death, Person: I0779, Gröndahl, Bernhard Efraimsson
W: Old age but no death, Person: I1061, , Gustaf Adolf Ulriksson
W: Old age but no death, Person: I1974, Flink, Stina
W: Disconnected individual, Person: I2009, Borg, Carl
W: Old age but no death, Person: I2228, Bergholm, Maria
W: Disconnected individual, Person: I0456, Höckert, Mathilda
W: Old age but no death, Person: I0176, Clayhills, Carl Christian
W: Old age but no death, Person: I1441, Puttro, Sara Davidsdotter
W: Old age but no death, Person: I1552, Brander, Kristian
W: Disconnected individual, Person: I1552, Brander, Kristian
W: Disconnected individual, Person: I0354, , Eric Nilsson
W: Old age but no death, Person: I0371, Stårck, Gabriel
W: Old age but no death, Person: I1466, Puttro, Adam Hinrichsson
W: Old age but no death, Person: I1913, Åhlberg, Eva Christina
W: Old age but no death, Person: I1992, Rosendahl, Justina
W: Disconnected individual, Person: I0470, Frej, N
W: Old age but no death, Person: I1291, , Maria Johansdotter
W: Old age but no death, Person: I1478, Putro, Eva Henriksdr.
W: Old age but no death, Person: I8928, , Kustava Juhanna Juhontytär
W: Disconnected individual, Person: I1555, Blåfield, Volter Ludvig Hannibal
W: Disconnected individual, Person: I1677, Piccander, Otto Severin
W: Old age but no death, Person: I2211, Wegelius, Esaias
W: Old age but no death, Person: I2244, Geitel, Petter Fredrik Alexander
W: Disconnected individual, Person: I0134, Florin, Elisabet
E: Birth equals death, Person: I0175, Clayhills, Anna Sophia
W: Old age but no death, Person: I10027, Lindell, Amanda
W: Old age but no death, Person: I1016, Alopæus, Brigitta (Brita) Elisabeth
W: Disconnected individual, Person: I0460, Hobin, Ebba
W: Disconnected individual, Person: I1594, Laurinus, Antti Joakim
W: Multiple parents, Person: I0483, Grään, Christina Juliana
W: Old age but no death, Person: I1455, Närjänen, Peter Henriksson
W: Old age but no death, Person: I2573, Eskola, Juho
W: Old age but no death, Person: I0935, Corsberg, Carl Andreas
W: Disconnected individual, Person: I1585, Virkki, Yrjö
W: Disconnected individual, Person: I0428, Unonius, Gustava
W: Old age but no death, Person: I2182, Parlin, Thomas Thomasson
W: Disconnected individual, Person: I0356, Wiberg, Maria Elisabet
W: Old age but no death, Person: I1335, , Gustaf Hinriksson
W: Old age but no death, Person: I1503, Putro, Elisabet Heinrichsdr.
W: Disconnected individual, Person: I1599, Klami, Daniel
W: Disconnected individual, Person: I2008, von Schantz, Augusta
W: Old age but no death, Person: I2246, Geitel, Ellen Alma Nashalia
W: Disconnected individual, Person: I0397, , Anna Mattsdotter
W: Old age but no death, Person: I0671, Kuhlberg, Lovisa Fredrica
W: Old age but no death, Person: I0606, Röngren, Bror
W: Disconnected individual, Person: I0472, Skogman, Fredrika
W: Old age but no death, Person: I0958, Torckill, Simon
W: Disconnected individual, Person: I0375, , Carin Olafsdotter
W: Disconnected individual, Person: I0441, Eschner, Fredrica
W: Disconnected individual, Person: I1139, Flodberg, Magnus Gottfrid
W: Disconnected individual, Person: I1949, Kemppi, Eva
W: Disconnected individual, Person: I0473, Edgren, N
W: Old age at death, Person: I2709, Pietilä, Gustava Ulriika Mikontytär
W: Disconnected individual, Person: I1586, Nyström, Kondrad Into (Inha)
W: Disconnected individual, Person: I0380, Mennander, Margareta Christina
W: Disconnected individual, Person: I1533, Rothström, Henrik Fabian
W: Old age but no death, Person: I1658, Lindwall, Birgitta
W: Disconnected individual, Person: I0197, Hartvall, Aleksandra Josefina
W: Old age but no death, Person: I1209, Granit, Selma Olivia
W: Old age but no death, Person: I1370, , Anna Lovisa Andersdotter
W: Disconnected individual, Person: I1556, Lehtonen, Karl Viktor
W: Old age but no death, Person: I2235, , Henrik Johan Henriksson
W: Disconnected individual, Person: I0191, Blåfield, August
W: Old age but no death, Person: I1506, Kappinen, Adam Andersson
W: Old age but no death, Person: I2199, Sandman, Johan
W: Disconnected individual, Person: I0383, Padolin, Daniel
W: Old age but no death, Person: I1513, Krane?, Ivana
W: Old age but no death, Person: I1509, Puttro, Anna Henrikova
W: Disconnected individual, Person: I0386, Norman, Johan
W: Old age but no death, Person: I1063, , Ulrik Leander Ulriksson
W: Disconnected individual, Person: I1622, Forsman, W.
W: Old age but no death, Person: I1483, Putro, Michel Mathiasson
W: Disconnected individual, Person: I1570, Peron, Karl Gustaf
W: Old age but no death, Person: I0351, Göhle, Johanna Elisabeth
W: Disconnected individual, Person: I1565, Blåfield, Knut Alexander
W: Disconnected individual, Person: I0476, Schogster, N
W: Old age but no death, Person: I1264, Nyberg, Hilma Fredrika
W: Old age but no death, Person: I2183, Parlin, Adam Thomasson
W: Disconnected individual, Person: I0307, Ylänen, Pirkko
W: Old age but no death, Person: I0465, Sucksdorff, Wendla
W: Old age but no death, Person: I0525, , Johan Johansson
W: Old age but no death, Person: I0582, Borg, Carl Jacob
W: Old age at death, Person: I0890, Hyppert, Christina
W: Old age but no death, Person: I1071, , Sofia Amanda Juhantytär
W: Old age but no death, Person: I1714, Sommer, Maria Josefina
W: Old age but no death, Person: I2197, Sandman, Anna Stina
W: Disconnected individual, Person: I0391, Hedman, Cathrina Margareta
W: Old age but no death, Person: I1523, Tallqvist, Henrik Johan
W: Disconnected individual, Person: I1523, Tallqvist, Henrik Johan
W: Disconnected individual, Person: I0595, Gräsbäck, Aurora
W: Disconnected individual, Person: I0594, Sibelius, E.
W: Old age but no death, Person: I0837, Ekerodde, Jacob
W: Old age but no death, Person: I2187, Stårck, Gabriel
W: Old age but no death, Person: I2572, , Michel Michelsson
W: Old age but no death, Person: I1025, Tesche, Henric Martin
W: Old age but no death, Person: I1502, Putro, Sophia Johansdr.
W: Old age but no death, Person: I1498, Kahi, Elisabeth Stephansdr.
W: Old age but no death, Person: I0520, Unonius, Carl Eric
W: Disconnected individual, Person: I0306, Grahn, Fredrika Gustafva
W: Old age but no death, Person: I1181, , Maria Esaiasdotter
E: Burial before death, Person: I2207, Hernberg, Gertrud Helena
W: Old age but no death, Person: I2236, , Lena Stina Carlsdotter
W: Disconnected individual, Person: I1541, Gadd, Ivar
W: Disconnected individual, Person: I1600, Turtola, Karl Gustaf
W: Old age but no death, Person: I1309, , Maria Henrichsdotter
W: Old age but no death, Person: I1850, Brunou, Georg
W: Disconnected individual, Person: I1850, Brunou, Georg
W: Disconnected individual, Person: I0461, Haartman, Inga Charlotta
W: Disconnected individual, Person: I0068, Lilius, August
W: Disconnected individual, Person: I0358, Wallgreen, Johannes
W: Old age but no death, Person: I0589, Borg, Catharina Magdalena
W: Disconnected individual, Person: I1142, Holmstén, Margareta Sofia
W: Old age but no death, Person: I0727, , Simon Mattsson
W: Disconnected individual, Person: I1447, Jääskeläinen, Anna Johannis
W: Disconnected individual, Person: I1544, Thuneberg, Otto Albert
W: Disconnected individual, Person: I0401, , Maria Olofsdotter
W: Old age but no death, Person: I0948, Torckill, Elias
W: Old age but no death, Person: I2214, Wegelius, Sofi Lisette Betty
W: Old age but no death, Person: I1399, Kiellroos, Maria Henrica
W: Old age but no death, Person: I1900, Sommer, Jonas Anthon
W: Disconnected individual, Person: I0138, Backborg, Johan
W: Disconnected individual, Person: I0365, Felin, Gustaf
W: Disconnected individual, Person: I1540, Dickström, Felix Konstantin
W: Old age but no death, Person: I1944, , Eric Johansson
W: Old age but no death, Person: I2243, Geitel, Anton Johan Alexander
W: Disconnected individual, Person: I1675, Piccander, Alfred
W: Old age but no death, Person: I1911, Belitz, Ivar Christian Carlsson
W: Old age but no death, Person: I0032, Utter, Johan Isaac
W: Disconnected individual, Person: I0189, Hartvall, Benhard
W: Old age but no death, Person: I1338, , Caisa Lisa Hindersdr.
W: Disconnected individual, Person: I0432, Unonius, Christina
W: Disconnected individual, Person: I1148, Gylling, Margareta Sofia
W: Old age but no death, Person: I1500, Hämäläinen, Johan Josephsson
W: Old age but no death, Person: I0301, Malm, Jacob
W: Disconnected individual, Person: I0395, , Brita Danielsdotter
W: Disconnected individual, Person: I0415, Sucksdorff, M.M.
W: Old age but no death, Person: I0507, Göhle, Israel Johan
W: Old age but no death, Person: I0871, Tesche, Johanna
W: Disconnected individual, Person: I1545, Stenroth, Karl Gideon
W: Disconnected individual, Person: I2088, Unonius, Elias
W: Old age but no death, Person: I2064, Trygg, Carl Gustaf
W: Disconnected individual, Person: I0044, Uggla, Gustaf L.
W: Disconnected individual, Person: I0308, Matilainen, Mervi
W: Old age but no death, Person: I0892, Hyppert, son
W: Old age but no death, Person: I1340, , Johan Andersson
W: Disconnected individual, Person: I1671, Berg, Axel
W: Old age but no death, Person: I1811, Polviander, Ulrika Sofia
W: Disconnected individual, Person: I0187, Stenius, Benedict
W: Disconnected individual, Person: I0200, Rotkirch, Helena
W: Old age but no death, Person: I1499, Putro, Katharina Johansdr.
W: Disconnected individual, Person: I1952, Pukonen, Margareta
W: Old age but no death, Person: I2103, Melart, Helena Emilia
W: Disconnected individual, Person: I0467, Frej, N
W: Old age but no death, Person: I0508, Göhle, Anna Wendla Elisabet
W: Old age but no death, Person: I0824, Ignatius, Petter Johan
W: Disconnected individual, Person: I1143, Tesche, N
W: Disconnected individual, Person: I2111, von Törnroth, Vera
W: Disconnected individual, Person: I0389, Amnorin, Maria Lovisa
W: Old age at death, Person: I0031, Sibelius, Jean
E: Baptism before birth, Person: I2240, Geitel, Nikolai Klas Alexander
W: Old age but no death, Person: I2240, Geitel, Nikolai Klas Alexander
W: Disconnected individual, Person: I0396, Alaperet, Staffan Johansson
W: Old age but no death, Person: I0932, Torckill, Carl
W: Disconnected individual, Person: I0355, , Henric Henricsson
W: Disconnected individual, Person: I0593, Sibelius, Maria
W: Old age but no death, Person: I1977, Flink, Anna Sophia
W: Old age but no death, Person: I0799, Heidenstrauch, Johannes
W: Old age but no death, Person: I1059, Björckstén, Johan
W: Old age but no death, Person: I1481, Heimonen, Anna Johansdr.
W: Old age but no death, Person: I0575, Utter, Beata Catharina
W: Old age but no death, Person: I0876, Tesche, Johanna Wilhelmina
W: Old age but no death, Person: I0938, Sundblad, Johan
W: Old age but no death, Person: I1956, Flink, Karl Johan
W: Old age but no death, Person: I1460, Puttro, Catharina Abrahamsdr.
W: Disconnected individual, Person: I1460, Puttro, Catharina Abrahamsdr.
W: Old age but no death, Person: I2101, Unonius, Lorents
W: Disconnected individual, Person: I0046, Mennander, Johan
W: Disconnected individual, Person: I0137, Carlstedt, Jonas
W: Disconnected individual, Person: I0388, Bruncrona, Anna Sophia
W: Disconnected individual, Person: I0065, Groundstroem, Georg Walter Edvard
E: Burial before death, Person: I2136, Blylod, Gustaf
W: Disconnected individual, Person: I0469, Brummert, N
W: Old age but no death, Person: I1428, Juvonen, Staffan Robert
W: Old age but no death, Person: I1543, Ahonius, Knut Hjalmar
W: Disconnected individual, Person: I1543, Ahonius, Knut Hjalmar
W: Old age but no death, Person: I1743, Saxelin, Helmi Maria
W: Old age but no death, Person: I2785, , Olga Eleonora Ulriksdotter
W: Old age but no death, Person: I0875, Tesche, Carl Alexander Joachim
W: Old age but no death, Person: I1976, Flink, Hedwig
W: Old age but no death, Person: I0973, Tesche, Johannes
W: Old age but no death, Person: I1501, Putro, Anders Johansson
W: Disconnected individual, Person: I0047, , Caisa Mattsdotter
W: Disconnected individual, Person: I0374, Zarlin, Thomas
W: Old age but no death, Person: I2732, , Johan Gustavsson
W: Old age but no death, Person: I1287, , Henrich Jakobsson
W: Old age but no death, Person: I2216, Wegelius, Jenny Pauline
W: Old age but no death, Person: I0685, Randelin, Andreas
W: Old age but no death, Person: I6443, , Juha Sigfrid Juhanpoika
W: Old age but no death, Person: I1636, Uhlwijk, Maria Catharina
W: Old age but no death, Person: I1936, Rautell, Thomas Ericsson
W: Old age but no death, Person: I2108, Yrjö-Koskinen, Lauri
W: Old age but no death, Person: I2176, Schrey, Eva Fredrika
W: Disconnected individual, Person: I0440, Unonius, Wendla
W: Old age but no death, Person: I0880, Tesche, Alexander Bernhard
W: Disconnected individual, Person: I1194, Rehbinder, Carl
W: Disconnected individual, Person: I1830, Neuman, Mickel
W: Old age but no death, Person: I0793, Ekerodde, Helena
W: Married often, Person: I1790, Uskelin, Johan Jacobsson
W: Disconnected individual, Person: I1423, Putro, Heikki
W: Old age but no death, Person: I1451, Närjänen, Henrik Mosesson
W: Old age but no death, Person: I1988, Naucler, Anna Sophia
W: Old age but no death, Person: I0038, , Karolina Heikintytär
W: Disconnected individual, Person: I0038, , Karolina Heikintytär
W: Old age but no death, Person: I0463, Sucksdorff, Adolf Mathias Israel
W: Old age but no death, Person: I1484, Putro, Zacharias Mathaisson
W: Disconnected individual, Person: I1525, Simola, August Alfred
W: Disconnected individual, Person: I0368, Lagermark, Margareta Christina
W: Late marriage, Family: F0394, , Johan Mattsson and , Walborg Henrichsdotter
W: Late marriage, Family: F0114, von Konow, Erik Berndt and Tavist, Eva Sofia
W: Late marriage, Family: F0279, , Johan Mattson and , Maria Johansdotter
W: Late marriage, Family: F0211, Ahlqvist, Matts and Elgman, Margareta
W: Late marriage, Family: F0471, Zilliacus, Alexander Benedict and Granit, Johanna Maria Albertina
W: Late marriage, Family: F0668, Glader, Eric and , Catharina Jacobsdotter
W: Large age differences between children, Family: F0853, Stårck, Gabriel and Wenander, Anna Maria
W: Large age differences between children, Family: F0330, Torckill, Gottfried and Sandheim, Christina
W: Early marriage, Family: F0404, , Matts Johansson and , Maria Johansdotter
W: Late marriage, Family: F0657, Saxelin, August and Lång, Hilda Augusta
W: Early marriage, Family: F0440, , Anders Jacobsson and , Sara Abrahamsdotter
W: Early marriage, Family: F0730, Jägerroos, Jakob Henrik and , Eva Helena Andersdotter
W: Early marriage, Family: F0831, Cremer, Henric and Blylod, Elsa Beata
W: Late marriage, Family: F0105, Törnström, Artturi and Tawaststjerna, Sofia Elisabet
W: Late marriage, Family: F0670, , Johan Henricsson and , Christina Jacobsdotter
W: Late marriage, Family: F0732, Belitz, Jacob Johan and Speitz, Eva Gustafsdotter
W: Early marriage, Family: F0209, Rivell, Johan and Randelin, Maria Juliana
W: Late marriage, Family: F0617, Sommers, Alexander Martinus and Taubenheim, Maria Vilhelmina
W: Early marriage, Family: F0064, Clayhills, Anthon Christiansson and Tesche, Anna Sophia
W: Young mother, Family: F0064, Clayhills, Anthon Christiansson and Tesche, Anna Sophia
W: Large age differences between children, Family: F0064, Clayhills, Anthon Christiansson and Tesche, Anna Sophia
W: Late marriage, Family: F0400, Cremer, Adolph Fredrich and Clayhills, Catharina Margaretha
W: Large age differences between children, Family: F0010, , Johan Johansson and Åkerberg, Catharina Fredrika
W: Husband and wife with the same surname, Family: F0213, Palenius, Samuel and Palenius, Anna Christina
W: Large age differences between children, Family: F0380, Björckstén, Richard and Unonius, Wilhelmina Dorothea
W: Old mother, Family: F0765, , Thomas Michelsson and , Sophia Pettersdotter
W: Early marriage, Family: F0841, von Numers, Fredric Mauritz and Schöring, Henrika
W: Late marriage, Family: F0085, Borg, Gabriel Carlsson and Österblad, Eva Catharina
W: Large age differences between children, Family: F0231, Randelin, Petter and Palenius, Johanna
W: Late marriage, Family: F0388, Eskola, Juho and , Anna Emerentia Davidsdotter
W: Early marriage, Family: F0624, Wegelius, David Davidsson and Wallenius, Fredrika Gabrielsdotter
W: Large age differences between children, Family: F0068, Molander, Johan and Tavast, Fredrika Lovisa
W: Late marriage, Family: F0671, Uskelin, Johan Jacobsson and , Eva Christina Johansdotter
W: Early marriage, Family: F0358, Dannenberg, Peter Henrichsson and Wallerian, Maria Christina
W: Large age difference between spouses, Family: F0709, af Forselles, Jacob and Schultz, Johanna Ulrica
W: Late marriage, Family: F0709, af Forselles, Jacob and Schultz, Johanna Ulrica
W: Large age differences between children, Family: F0307, Qvist, Elias and Elfwengren, Anna
W: Late marriage, Family: F0249, , Anders Jacobsson and , Maria Johansdotter
W: Large age differences between children, Family: F0187, Sibelius, Christian and Swan, Kaino Ihanelma
W: Late marriage, Family: F0291, Sipilä, Reinhold Juhonpoika and Lindell, Amanda
W: Large age differences between children, Family: F0269, Lindholm, Abraham Henricsson and Gröndahl, Fredrika Juhantytär
W: Late marriage, Family: F0077, Åkerberg, Mathias Andersson and Björkman, Johanna Henriksdotter
W: Late marriage, Family: F0232, Randelin, Petter and Blom, Hedvig Johanna
W: Late marriage, Family: F0674, Uskelin, Johan Jacobsson and , Maria Ulrica Henricsdotter
W: Large age differences between children, Family: F0443, , Jacob Jacobsson and , Walborg Simonsdotter
W: Large age differences between children, Family: F0530, Putro, Matthias Adamsson and Kaipiainen, Maria Mosesdotter
W: Large age differences between children, Family: F0045, , Henrik Mattsson and , Greta Gustafsdotter
W: Late marriage, Family: F0270, Gröndahl, Bernhard Efraimsson and Gröndahl, Fredrika Juhantytär
W: Large age differences between children, Family: F0152, Stenius, Bengt and Backman, Anna Maria
W: Late marriage, Family: F0737, Martila, Mårten Johansson and , Hedvig Andersdotter
W: Large age differences between children, Family: F0839, Schöring, Anders and Kreander, Sara
W: Early marriage, Family: F0539, Blåfield, Henrik and von Birckholtz, Eva Catarina Gustafsdotter
W: Large age differences between children, Family: F0518, Ilmonius, Abraham and Hellenius, Maria Christina
W: Large age differences between children, Family: F0008, , Matts Mårtensson and , Anna Andersdotter
W: Large age differences between children, Family: F0050, Bruun, Henric Jacob and Boisman, Beata Catharina
W: Late marriage, Family: F0408, Hasula, Matts and Grambou, Maria Sophia
W: Late marriage, Family: F0439, Blomlöf, Efraim Johansson and , Maria Esaiasdotter
W: Large age differences between children, Family: F0533, Schreij, Johan Adolf and Gottsman, Lowisa Ulrika
W: Early marriage, Family: F0226, Randelin, Gabriel and Sevon, Margareta Sophia
done

"""

test_output = None

def gramps_verify(gramps_runner, username, xmlfile):
    if test_output:
        lines = test_output.splitlines()
        import time
        time.sleep(3)
    else:
        upload_folder = get_upload_folder(username) 
        pathname = os.path.join(upload_folder, xmlfile)
        #cmd = f"unset PYTHONPATH;env;"
        #cmd += f"rm -rf ~/{xmlfile}.media;"
        #cmd += f"/usr/bin/gramps -i {pathname} -a tool -p name=verify" #.split()
        cmd = [gramps_runner, xmlfile, pathname]
        cmd = f"{gramps_runner} '{xmlfile}' '{pathname}'"
        print("cmd:",cmd)
        res = subprocess.run(cmd, shell=True, capture_output=True, encoding="utf-8")
        print(res.stderr)
        lines = res.stdout.splitlines()
    rsp = defaultdict(list)
    for line in lines:
        if line[1:2] == ":":
            msgtype, _msg = line.split(",", maxsplit=1)
            rsp[msgtype.strip()].append(line)
    return rsp


