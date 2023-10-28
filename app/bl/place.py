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
    - PlaceReaderTx  has methods for reading Place and connected data
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

logger = logging.getLogger("stkserver")

from .base import NodeObject, Status
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

    def __init__(self, iid=None):
        """Creates a new Place instance."""
        NodeObject.__init__(self, iid)
        #! self.uniq_id = uniq_id
        self.type = ""
        self.names = []
        self.pname = ""
        self.coord = None

    def __str__(self):
        return f"{self.uniq_id} {self.pname} ({self.type})"

    def coord_letter(self, precision=2):
        """ Show coordinates with principal compass point letters using user language. 

            Examples:
                59°49′25″N, 22°58′05″E -> 59.8236 N, 22.9680 E
                12°5′35″S, 77°2′47″ W -> -12.093056, -77.046389 -> 12.0930 S, 77.0463 W
        """
        if self.coord and isinstance(self.coord, list):
            east = self.coord[0]
            north = self.coord[1]
            if east >= 0 and north >= 0:
                return f"{east:6.{precision}f} E, {north:6.{precision}f} N"
            elif east >= 0 and north < 0:
                return f"{east:6.{precision}f} E, {-north:6.{precision}f} S"
            elif east < 0 and north < 0:
                return f"{-east:6.{precision}f} W, {-north:6.{precision}f} S"
            else: # east < 0 and north >= 0:
                return f"{-east:6.{precision}f} W, {north:6.{precision}f} N"
        else:
            return ""

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

    def __init__(self, iid=None, ptype="", level=None):
        """Creates a new PlaceBl instance.

        You may also give for printout eventual hierarchy level
        """
        Place.__init__(self, iid)

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
                        selection[lang] = name.iid
            # 2. find replacing languages, if not matching
            for lang in use_langs:
                if not lang in selection.keys():
                    # Maybe a missing language is found?
                    for name in names:
                        if name.lang == "" and not lang in selection.keys():
                            # print(f'# select {lang}>{name.lang}: {name.name} {name.uniq_id}')
                            selection[lang] = name.iid
                if not lang in selection.keys():
                    # No missing language, select any
                    for name in names:
                        if not lang in selection.keys():
                            # print(f'# select {lang}>{name.lang}: {name.name} {name.uniq_id}')
                            selection[lang] = name.iid

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

        The pl_tuple has Places data as a tuple 
        [[28101, "b16a6ee2c7a24e399d45554faa8fb094", "City", "Lovisa", "sv"]].

        If a Place exists twice, their names are combined.
        If there is a language code, it is appended in parenthesis.

        TODO. Lajittele paikannimet kielen mukaan (si, sv, <muut>, "")
              ja aakkosjärjestykseen
        """
        placedict = {}
        for nid, iid, ntype, name, nlang in pn_tuples:
            if nid:  # id of a lower place
                pn = PlaceName(name=name, lang=nlang)
                if nid in placedict:
                    # Append name to existing PlaceBl
                    placedict[nid].names.append(pn)
                    placedict[nid].names.sort()
                else:
                    # Add a new PlaceBl
                    p = PlaceBl(nid)
                    p.iid = iid
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
        """Arrange Place_name objects by name usefulness.

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


class PlaceReaderTx(DataService):
    """
    Abstracted Place datastore for reading.

    Data reading class for Place objects with associated data.

    - Methods return a dict result object {'status':Status, ...}
    """

    # def __init__(self, service_name: str, u_context=None):
    #     # print(f'#~~{self.__class__.__name__} init')
    #     super().__init__(service_name, u_context)
    #     # obj_catalog maps object uniq_id to connected objects
    #     self.obj_catalog = {}  # dict {uniq_id: Connected_object: NodeObject}


    def get_place_list(self):
        """Get a list on PlaceBl objects with nearest hierarchy neighbors.

        Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat
        """
        context = self.user_context
        fw = context.first  # From here forward
        use_user = context.batch_user()
        places = self.dataservice.tx_get_place_list_fw(
            use_user, fw, context.count, lang=context.lang,
            material=context.material,
        )
        # for p in places:
        #     oth_names = []
        #     for node in record["names"]:
        #         oth_names.append(PlaceName_from_node(node))            # Arrage names by local language first
        #     lst = PlaceName.arrange_names(oth_names)
        #
        #     p.names += lst
        #     p.pname = p.names[0].name
        #     p.uppers = PlaceBl.combine_places(record["upper"], lang)
        #     p.lowers = PlaceBl.combine_places(record["lower"], lang)

        # Update the page scope according to items really found
        if places:
            print(
                f"PlaceReaderTx.get_place_list: {len(places)} places "
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
            print(f"bl.place.PlaceReaderTx.get_place_list: no places")
            return {
                "status": Status.NOT_FOUND,
                "items": [],
                "statustext": f'No places fw="{fw}"',
            }
        return {"items": places, "status": Status.OK}

    def get_place_data(self, iid):
        """Read the place hierarchy and events connected to this place.

        Luetaan annettuun paikkaan liittyvä hierarkia ja tapahtumat
        Palauttaa paikkahierarkian ja (henkilö)tapahtumat.

        """
        # Get a Place with Names, Notes and Medias
        use_user = self.user_context.batch_user()
        privacy = self.user_context.is_common()
        lang = self.user_context.lang
        material = self.user_context.material
        res = self.dataservice.tx_get_place_w_names_citations_notes_medias(
                    use_user, iid, lang, material)
        # res {place:Place, uniq_ids:list(uniq_ids), "citas": list(Citations)}
        # The uniq_ids includes all references to names, notes, medias and citations
        place = res.get("place")
        results = {"place": place, "status": Status.OK}

        if not place:
            res = {
                "status": Status.ERROR,
                "statustext": f"No Place '{iid}'",
            }
            return res

        try:
            results["hierarchy"] = self.dataservice.tx_get_place_tree(
                place.iid, lang=lang
            )

        except AttributeError as e:
            traceback.print_exc()
            return {
                "status": Status.ERROR,
                "statustext": f"Place tree attr for {place.iid}: {e}",
            }
        except ValueError as e:
            return {
                "status": Status.ERROR,
                "statustext": f"Place tree value for {place.uiid}: {e}",
            }

        results["uniq_ids"]= res.get("uniq_ids",[])
        citations = res.get("citas", [])
        if citations:
            results["citations"] = citations

        res = self.dataservice.tx_get_place_events(place.iid, privacy)
        results["events"] = res["items"]
        return results

    def get_citation_sources_repositories(self, citations):
        """ Get source citations for given Place. """
        if not citations:
            return []

        # Find (c:Citation) -> (s:Source) --> (a:Repository)
        res = self.dataservice.tx_get_citation_sources_repositories(citations)
        refs = res.get("sources", [])
        for c in citations:
            if hasattr(c, 'source_refs'):
                c.source_refs.append(refs[c.uniq_id])
            else:
                c.source_refs = [refs[c.uniq_id]]
        return res

    def get_placename_list(self, count=40, by_cites=False):
        """
        Return placename stats so that the names can be displayed in a name cloud.
        
        If by_cites, the citations of the place are calculate; 
        else calculate all inner places.
        """
        ds = self.dataservice
        if by_cites: # experimental rule
            placenames = ds.tx_get_citated_placename_list(self.use_user, 
                                              self.user_context.material,
                                              count=count)
        else:
            placenames = ds.tx_get_placename_list(self.use_user, 
                                              self.user_context.material,
                                              count=count)
        # Returns [{placename, count, iid},...]
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
                self.dataservice.tx,
                place.uniq_id, def_names["fi"], def_names["sv"]
            )

            ret = self.dataservice.ds_commit()
            st = ret.get("status")
            return {
                "status": st,
                "place": place,
                "statustext": ret.get("statustext", ""),
            }
