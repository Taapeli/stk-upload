'''
Created on 12.3.2020

@author: jm
'''

class Point:
    """ Paikan koordinaatit

        Properties:
            coord   coordinates of the point as list [lat, lon]
                    (north, east directions in degrees)
    """
    _point_coordinate_tr = str.maketrans(',°′″\\\'"NESWPIEL', '.              ')


    def __init__(self,  lon,  lat=None):
        """ Create a new Point instance.
            Arguments may be:
            - lon(float), lat(float)    - real coordinates
            - lon(str), lat(str)        - coordinates to be converted
            - [lon, lat]                - ready coordinate vector (list or tuple)
        """
        self.coord = None
        try:
            if isinstance(lon, (list, tuple)):
                # is (lon, lat) or [lon, lat]
                if len(lon) >= 2 and \
                        isinstance(lon[0], float) and isinstance(lon[1], float):
                    self.coord = list(lon)    # coord = [lat, lon]
                else:
                    raise(ValueError, "Point({}) are not two floats".format(lon))
            else:
                self.coord = [lon, lat]

            # Now the arguments are in self.coord[0:1]

            ''' If coordinate value is string, the characters '°′″'"NESWPIEL'
                and '\' are replaced by space and the comma by dot with this table.
                (These letters stand for North, East, ... Pohjoinen, Itä ...)
            '''

            for i in list(range(len(self.coord))):   # [0,1]
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
                            if len(a) == 3:     # There are minutes and second
                                minutes = float(a[1])
                                seconds = float(a[2])
                                self.coord[i] = degrees + minutes/60. + seconds/3600.
                            else:               # There are no seconds
                                minutes = float(a[1])
                                self.coord[i] = degrees + minutes/60.
                        else:                   # Only degrees
                                self.coord[i] = degrees
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

