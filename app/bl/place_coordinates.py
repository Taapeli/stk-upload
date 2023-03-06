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

"""
Created on 12.3.2020

@author: jm
"""
# blacked 2021-05-01 JMä


class Point:
    """Paikan koordinaatit

    Properties:
        coord   coordinates of the point as list [lat, lon]
                (north, east directions in floating degrees)

    Note.
        You may use Place.coord_letter(precision) method to display 
        coordinates with N,E marks: "61.2037 E, 24.0606 N"
    """

    _point_coordinate_tr = str.maketrans(",°′″\\'\"NESWPIEL", ".              ")

    def __init__(self, lat, lon=None):
        """Create a new Point instance.
        Arguments may be:
        - lat(float), lon(float)    - real coordinates (north, east)
        - lat(str), lon(str)        - coordinates to be converted
        - [lat, lon]                - ready coordinate vector (list or tuple)
        
        Example lat, lon: [63.97, '024°16′56″E']
        """
        self.coord = None
        try:
            if isinstance(lat, (list, tuple)):
                # is (lat, lon) or [lat, lon]
                if (
                    len(lat) >= 2
                    and isinstance(lat[0], float)
                    and isinstance(lat[1], float)
                ):
                    self.coord = list(lat)  # coord = [lat, lon]
                else:
                    raise (ValueError, "Point({}) is not two floats".format(lat))
            else:
                self.coord = [lat, lon]

            # Now the arguments are in self.coord[0:1]

            """ If coordinate value is string, the characters '°′″'"NESWPIEL'
                and '\' are replaced by space and the comma by dot with this table.
                (These letters stand for North, East, ... Pohjoinen, Itä ...)
            """

            #print(f"#bl.place_coordinates.Point {self.coord}")
            for i in list(range(len(self.coord))):  # [0,1]
                # If a coordinate is float, it's ok
                x = self.coord[i]
                if not isinstance(x, float):
                    if not x:
                        raise ValueError("Point arg empty ({})".format(self.coord))
                    if isinstance(x, str):
                        # String conversion to float:
                        #   example "60° 37' 34,647N" gives ['60', '37', '34.647']
                        #   and "26° 11\' 7,411"I" gives
                        a = x.translate(self._point_coordinate_tr).split()
                        if not a:
                            raise ValueError("Point arg error {}".format(self.coord))
                        degrees = float(a[0])
                        if len(a) > 1:
                            if len(a) == 3:  # There are minutes and second
                                minutes = float(a[1])
                                seconds = float(a[2])
                                self.coord[i] = (
                                    degrees + minutes / 60.0 + seconds / 3600.0
                                )
                            else:  # There are no seconds
                                minutes = float(a[1])
                                self.coord[i] = degrees + minutes / 60.0
                        else:  # Only degrees
                            self.coord[i] = degrees
                        # Negative directions given by trailing letter
                        if i == 0: # latitude
                            if x[-1] in "SE":  # south, etelä, syd
                                self.coord[i] = self.coord[i] * -1                        
                                #print(f"#south {x[-1]} = {self.coord[i]}")
                        else: # longitude
                            if x[-1] in "WLV":  #bl.place_coordinates.Point:West, länsi or vest
                                self.coord[i] = self.coord[i] * -1
                                #print(f"#bl.place_coordinates.Point:west {x[-1]} = {self.coord[i]}")
                    else:
                        raise ValueError("Point arg type is {}".format(self.coord[i]))
        except:
            raise

    def __str__(self):
        if self.coord:
            return "({:0.4f}, {:0.4f})".format(self.coord[0], self.coord[1])
        else:
            return ""

    def get_coordinates(self):
        """ Return the Point coordinates as list (leveys- ja pituuspiiri) """

        return self.coord
