'''
Created on 23.3.2020

@author: jm
'''
import logging 
from bl.place import PlaceBl, PlaceName
from bl.source import SourceBl
from pe.neo4j.nodereaders import PlaceName_from_node, PlaceBl_from_node,\
    SourceBl_from_node

from pe.neo4j.cypher.cy_place import CypherPlace
from pe.neo4j.cypher.cy_gramps import CypherObjectWHandle

logger = logging.getLogger('stkserver')

class Neo4jWriteDriver(object):
    '''
    classdocs
    '''

    def __init__(self, dbdriver, tx):
        ''' Create a writer/updater object with db driver and user context.
        '''
        self.dbdriver = dbdriver
        self.tx = tx
    
        
    def place_set_default_names(self, place_id, fi_id, sv_id):
        ''' Creates default links from Place to fi and sv PlaceNames.

            - place_id      Place object id
            - fi_id         PlaceName object id for fi
            - sv_id         PlaceName object id for sv
        '''
        try:
            if fi_id == sv_id:
                result = self.tx.run(CypherPlace.link_name_lang_single, 
                                     place_id=place_id, fi_id=fi_id)
            else:
                result = self.tx.run(CypherPlace.link_name_lang, 
                                     place_id=place_id, fi_id=fi_id, sv_id=sv_id)
            x = None
            for x, _fi, _sv in result:
                #print(f"# Linked ({x}:Place)-['fi']->({fi}), -['sv']->({sv})")
                pass

            if not x:
                logger.warning("eo4jWriteDriver.place_set_default_names: not created "
                     f"Place {place_id}, names fi:{fi_id}, sv:{sv_id}")

        except Exception as err:
            logger.error(f"Neo4jWriteDriver.place_set_default_names: {err}")
            return err


    def media_save_w_handles(self, iid:str, media_refs:list):
        ''' NOT USED! Save media object and it's Note and Citation references
            using their Gramps handles.
            
            handle:
                handle      # Media object handle
                media_order       # Media reference order nr
                crop              # Four coordinates
                note_handles      # list of Note object handles
                citation_handles  # list of Citation object handles
        '''
        doing = "?"
        try:
            for resu in media_refs:
                r_attr = {'order':resu.media_order}
                if resu.crop:
                    r_attr['left'] = resu.crop[0]
                    r_attr['upper'] = resu.crop[1]
                    r_attr['right'] = resu.crop[2]
                    r_attr['lower'] = resu.crop[3]
                doing = f"(src:{iid}) -[{r_attr}]-> Media {resu.handle}"
#                 print(doing)
                self.tx.run(CypherObjectWHandle.link_media,
                            lbl=resu.obj_name,
                            root_id=iid,
                            handle=resu.handle, 
                            r_attr=r_attr)
                media_uid = iid    # for media object

                for handle in resu.note_handles:
                    doing = f"{media_uid}->Note {handle}"
#                     result = self.tx.run('MATCH (s), (t) WHERE ID(s)=$root_id and t.handle=$handle RETURN s,t', 
#                         root_id=media_uid, handle=handle)
#                     for s,t in result: print(f"\nMedia {s}\nNote {t}")
                    self.tx.run(CypherObjectWHandle.link_note, 
                                lbl=resu.obj_name,
                                root_id=media_uid,
                                handle=handle)

                for handle in resu.citation_handles:
                    doing = f"{media_uid}->Citation {handle}"
#                     result = self.tx.run('MATCH (s), (t) WHERE ID(s)=$root_id and t.handle=$handle RETURN s,t', 
#                         root_id=media_uid, handle=handle)
#                     for s,t in result: print(f"\nMedia {s}\nCite {t}")
                    self.tx.run(CypherObjectWHandle.link_citation, 
                                lbl=resu.obj_name,
                                root_id=media_uid,
                                handle=handle)

        except Exception as err:
            logger.error(f"Neo4jWriteDriver.media_save_w_handles {doing}: {err}")



    def mergeplaces(self, id1, id2):
        cypher_delete_namelinks = """
            match (node) -[r:NAME_LANG]-> (pn)
            where id(node) = $id
            delete r
        """
        cypher_mergeplaces = """
            match (p1:Place)        where id(p1) = $id1 
            match (p2:Place)        where id(p2) = $id2
            call apoc.refactor.mergeNodes([p1,p2],
                {properties:'discard',mergeRels:true})
            yield node
            with node
            match (node) -[r2:NAME]-> (pn2)
            return node, collect(pn2) as names
        """
        self.tx.run(cypher_delete_namelinks,id=id1).single()
        rec = self.tx.run(cypher_mergeplaces,id1=id1,id2=id2).single()
        node = rec['node']
        place = PlaceBl_from_node(node)
        name_nodes = rec['names']
        name_objects = [PlaceName_from_node(n) for n in name_nodes]
        return place, name_objects

    def mergesources(self, id1, id2):
        cypher_mergesources = """
            match (p1:Source)        where id(p1) = $id1 
            match (p2:Source)        where id(p2) = $id2
            call apoc.refactor.mergeNodes([p1,p2],
                {properties:'discard',mergeRels:true})
            yield node
            return node
        """
        rec = self.tx.run(cypher_mergesources,id1=id1,id2=id2).single()
        if rec is None: return None
        node = rec['node']
        source = SourceBl_from_node(node)
        return source
        