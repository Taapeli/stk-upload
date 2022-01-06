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
    Placeclasses: Place, PlaceBl, SPlaceReader and PlaceName.

    - Place        represents Place Node in database
    - PlaceBl      represents Place and connected data (was Place_combo)
    - PlaceReader  has methods for reading Place and connected data
                   called from ui routes.py

Created on 11.3.2020 in bl.place
@author: jm

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py
@author: jm

Todo:
    Miten paikkakuntiin saisi kokoluokituksen? Voisi näyttää sopivan zoomauksen karttaan
    1. _Pieniä_ talo, kortteli, tontti, tila,  rakennus
    2. _Keskikokoisia_ kylä, kaupunginosa, pitäjä, kaupunki, 
    3. _Suuria_ maa, osavaltio, lääni
    - Loput näyttäisi keskikokoisina

"""
# blacked 2021-05-01 JMä
import traceback
import logging
#import shareds

logger = logging.getLogger("stkserver")

from .base import NodeObject, Status
from bl.dates import DateRange
from pe.dataservice import DataService


class Place(NodeObject):
    """Place / Paikka:

    Properties:
        Defined in NodeObject:
            change
            id                  esim. "P0001"
            type                str paikan tyyppi
            pname               str paikan nimi
        May be defined in PlaceBl:
            names[]             PlaceName
            coord               str paikan koordinaatit (leveys- ja pituuspiiri)
            surrounding[]       int uniq_ids of upper
            note_ref[]          int uniq_ids of Notes
            media_ref[]         int uniq_ids of Medias
        May be defined in Place_gramps:
            surround_ref[]      dictionaries {'hlink':handle, 'dates':dates}
            citation_ref[]      int uniq_ids of Citations
            placeref_hlink      str paikan osoite
            note_handles       str huomautuksen osoite (tulostuksessa Note-olioita)
    """

    def __init__(self, uniq_id=None):
        """Creates a new Place instance."""
        NodeObject.__init__(self)
        self.uniq_id = uniq_id
        self.type = ""
        self.names = []
        self.pname = ""
        self.coord = None

    def __str__(self):
        return f"{self.uniq_id} {self.pname} ({self.type})"


class PlaceBl(Place):
    """Place / Paikka:

    Properties, might be defined in here:
            names[]             PlaceName default name first
            coord               str paikan koordinaatit (leveys- ja pituuspiiri)
            surrounding[]       int uniq_ids of upper
            note_ref[]          int uniq_ids of Notes
            media_ref[]         int uniq_ids of Medias
        May be defined in Place_gramps:
            surround_ref[]      dictionaries {'hlink':handle, 'dates':dates}
            citation_ref[]      int uniq_ids of Citations
            placeref_hlink      str paikan osoite
            note_handles       str huomautuksen osoite (tulostuksessa Note-olioita)
    """

    def __init__(self, uniq_id=None, ptype="", level=None):
        """Creates a new PlaceBl instance.

        You may also give for printout eventual hierarchy level
        """
        Place.__init__(self, uniq_id)

        if ptype:
            self.type = ptype
        self.names = []
        if level != None:
            self.level = level

        self.uppers = []  # Upper place objects for hierarchy display
        self.notes = []  # Notes connected to this place
        self.note_ref = []  # uniq_ids of Notes
        self.media_ref = []  # uniq_id of models.gen.media.Media
        self.ref_cnt = None  # for display: count of referencing objects

    def set_default_names(self, tx, def_names: dict, dataservice):
        """Creates default links from Place to fi and sv PlaceNames.

        The objects are referred with database id numbers.

        - place         Place object
        - - .names      PlaceName objects
        - def_names     dict {lang, uid} uniq_id's of PlaceName objects
        """
        dataservice.ds_place_set_default_names(tx, self.uniq_id, def_names["fi"], def_names["sv"])

    @staticmethod
    def find_default_names(names: list, use_langs: list):
        """Select default names for listed use_langs list.

        Rules for name selection
        - if a Place_name with given lang ('if') is found, use it
        - else if a Place_name with no lang ('') is found, use it
        - else use any name
        """
        if not names:
            return {"status": Status.ERROR, "ids": {}}
        selection = {}
        # print(f'# ---- Place {names[0].name}')
        try:
            # 1.     find matching languages for use_langs
            for lang in use_langs:
                for name in names:
                    if name.lang == lang and not lang in selection.keys():
                        # A matching language
                        # print(f'# select {lang}: {name.name} {name.uniq_id}')
                        selection[lang] = name.uniq_id
            # 2. find replacing languages, if not matching
            for lang in use_langs:
                if not lang in selection.keys():
                    # Maybe a missing language is found?
                    for name in names:
                        if name.lang == "" and not lang in selection.keys():
                            # print(f'# select {lang}>{name.lang}: {name.name} {name.uniq_id}')
                            selection[lang] = name.uniq_id
                if not lang in selection.keys():
                    # No missing language, select any
                    for name in names:
                        if not lang in selection.keys():
                            # print(f'# select {lang}>{name.lang}: {name.name} {name.uniq_id}')
                            selection[lang] = name.uniq_id

            ret = {}
            for lang in use_langs:
                ret[lang] = selection[lang]
            return {"status": Status.OK, "ids": ret}

        except Exception as e:
            logger.error(f"bl.place.PlaceBl.find_default_names {selection}: {e}")
            return {"status": Status.ERROR, "items": selection}


    @staticmethod
    def combine_places(pn_tuples, lang):
        """Creates a list of Places with names combined from given names.

        The pl_tuple has Places data as a tuple [[28101, "City", "Lovisa", "sv"]].

        Jos sama Place esiintyy uudestaan, niiden nimet yhdistetään.
        Jos nimeen on liitetty kielikoodi, se laitetaan sulkuihin mukaan.

        TODO. Lajittele paikannimet kielen mukaan (si, sv, <muut>, "")
              ja aakkosjärjestykseen
        """
        placedict = {}
        for nid, nuuid, ntype, name, nlang in pn_tuples:
            if nid:  # id of a lower place
                pn = PlaceName(name=name, lang=nlang)
                if nid in placedict:
                    # Append name to existing PlaceBl
                    placedict[nid].names.append(pn)
                    placedict[nid].names.sort()
                else:
                    # Add a new PlaceBl
                    p = PlaceBl(nid)
                    p.uuid = nuuid
                    p.type = ntype
                    p.names.append(pn)
                    placedict[nid] = p
        place_list = list(placedict.values())
        for p in place_list:
            p.names = PlaceName.arrange_names(p.names, lang)
            p.pname = p.names[0]
        return place_list


class PlaceName(NodeObject):
    """Paikan nimi

    Properties:
            name             str nimi
            lang             str kielikoodi
            dates            DateRange aikajakso
            order            int display order of various names of a place
    """

    def __init__(self, name="", lang=""):
        """ Luo uuden name-instanssin """
        self.name = name
        self.lang = lang
        self.dates = None
        self.order = 0

    def __str__(self):
        if self.dates:
            d = "/" + str(self.dates)
        else:
            d = ""
        if self.lang != "":
            return f"'{self.name}' ({self.lang}){d}"
        else:
            return f"'{self.name}'{d}"


    @staticmethod
    def arrange_names(namelist: list, lang: str = None):
        """Arrange Place_name objects by name usefullness.

        If lang attribute is present, the default language name is processed
        outside this method.

        Order:
        - First local names fi, sv
        - Then names without lang
        - Last other language names
        """
        n_default = []
        n_local = []
        n_unknown = []
        n_other = []
        if lang == "fi":
            other_lang = "sv"
        elif lang == "sv":
            other_lang = "fi"
        else:
            other_lang = None
        for nm in namelist:
            if lang != None and nm.lang == lang:
                n_local.append(nm)
            elif nm.lang in ["fi", "sv"] and nm.lang != other_lang:
                n_local.append(nm)
            elif nm.lang == "":
                n_unknown.append(nm)
            else:
                n_other.append(nm)
        return n_default + n_local + n_unknown + n_other

    def _lang_key(self, obj):
        """ Name comparison key by 1) language, 2) name """
        lang_order = {
            "fi": "0",
            "sv": "1",
            "vi": "2",
            "de": "3",
            "la": "4",
            "ru": "5",
            "": "6",
        }
        if obj:
            if obj.lang in lang_order.keys():
                return lang_order[obj.lang] + ":" + obj.name
            return "x:" + obj.name
        return ""

    def __lt__(self, other):
        a = self._lang_key(self)
        b = self._lang_key(other)
        return a < b

    def __le__(self, other):
        return self._lang_key(self) <= self._lang_key(other)

    def __eq__(self, other):
        return self._lang_key(self) == self._lang_key(other)

    def __ge__(self, other):
        return self._lang_key(self) >= self._lang_key(other)

    def __gt__(self, other):
        return self._lang_key(self) > self._lang_key(other)

    def __ne__(self, other):
        return self._lang_key(self) != self._lang_key(other)


class PlaceReader(DataService):
    """
    Abstracted Place datastore for reading.

    Data reading class for Place objects with associated data.

    - Methods return a dict result object {'status':Status, ...}
    """

    def get_place_list(self):
        """Get a list on PlaceBl objects with nearest hierarchy neighbors.

        Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat
        """
        context = self.user_context
        fw = context.first  # From here forward
        use_user = context.batch_user()
        places = self.dataservice.dr_get_place_list_fw(
            use_user, fw, context.count, lang=context.lang,
            material=context.material,
        )

        # Update the page scope according to items really found
        if places:
            print(
                f"PlaceReader.get_place_list: {len(places)} places "
                f'{context.direction} "{places[0].pname}" – "{places[-1].pname}"'
            )
            context.update_session_scope(
                "place_scope",
                places[0].pname,
                places[-1].pname,
                context.count,
                len(places),
            )
        else:
            print(f"bl.place.PlaceReader.get_place_list: no places")
            return {
                "status": Status.NOT_FOUND,
                "items": [],
                "statustext": f'No places fw="{fw}"',
            }
        return {"items": places, "status": Status.OK}

    def get_places_w_events(self, uuid):
        """Read the place hierarchy and events connected to this place.

        Luetaan annettuun paikkaan liittyvä hierarkia ja tapahtumat
        Palauttaa paikkahierarkian ja (henkilö)tapahtumat.

        """
        # Get a Place with Names, Notes and Medias
        use_user = self.user_context.batch_user()
        privacy = self.user_context.is_common()
        lang = self.user_context.lang
        material = self.user_context.material
        res = self.dataservice.dr_get_place_w_names_notes_medias(use_user, uuid,
                                                                 lang, material)
        place = res.get("place")
        results = {"place": place, "status": Status.OK}

        if not place:
            res = {
                "status": Status.ERROR,
                "statustext": f"get_places_w_events: No Place with uuid={uuid}",
            }
            return res

        # TODO: Find Citation -> Source -> Repository for each uniq_ids
        try:
            results["hierarchy"] = self.dataservice.dr_get_place_tree(
                place.uniq_id, lang=lang
            )

        except AttributeError as e:
            traceback.print_exc()
            return {
                "status": Status.ERROR,
                "statustext": f"Place tree attr for {place.uniq_id}: {e}",
            }
        except ValueError as e:
            return {
                "status": Status.ERROR,
                "statustext": f"Place tree value for {place.uniq_id}: {e}",
            }

        res = self.dataservice.dr_get_place_events(place.uniq_id, privacy)
        results["events"] = res["items"]
        return results

    def get_placename_list(self, count=40):
        """
        Return placename stats so that the names can be displayed in a name cloud.
        """
        ds = self.dataservice
        placenames = ds.dr_get_placename_list(self.use_user, 
                                              self.user_context.material,
                                              count=count)
        # Returns [{'surname': surname, 'count': count},...]

        # if self.use_user:
        #     placename_stats = self.dataservice.dr_get_placename_stats_by_user(
        #         self.use_user, count=count
        #     )
        # else:
        #     placename_stats = self.dataservice.dr_get_placename_stats_common(
        #         count=count
        #     )
        return placenames


class PlaceUpdater(DataService):
    """
    Abstracted Place datastore for read/update with transaction.

    Data update class for Place objects with associated data.

    - Methods return a dict result object {'status':Status, ...}
    """

    def merge2places(self, id1, id2):
        """Merges two places"""
        # Check that given nodes are included in the same Batch or Audit node
        ret = self.dataservice.ds_merge_check(id1, id2)
        if Status.has_failed(ret):
            self.dataservice.ds_rollback()
            return ret

        # Merge nodes
        ret = self.dataservice.ds_places_merge(id1, id2)
        if Status.has_failed(ret):
            self.dataservice.ds_rollback()
            return ret

        place = ret.get("place")
        # Select default names for default languages
        ret = PlaceBl.find_default_names(place.names, ["fi", "sv"])
        if Status.has_failed(ret):
            self.dataservice.ds_rollback()
            return ret
        st = ret.get("status")
        if st == Status.OK:
            # Update default language name links
            def_names = ret.get("ids")
            self.dataservice.ds_place_set_default_names(
                place.uniq_id, def_names["fi"], def_names["sv"]
            )

            ret = self.dataservice.ds_commit()
            st = ret.get("status")
            return {
                "status": st,
                "place": place,
                "statustext": ret.get("statustext", ""),
            }
