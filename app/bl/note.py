"""
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

Changed 13.6.2018/JMä: get_notes() result from list(str) to list(Note)

@author: jm
"""

# blacked 25.5.2021/JMä
from sys import stderr

from bl.base import NodeObject
from pe.neo4j.cypher.cy_note import CypherNote
from pe.dataservice import DataService

# from models.gen.cypher import Cypher_note
# from models.cypher_gramps import Cypher_note_in_batch # Cypher_note_w_handle,
# import shareds


class Note(NodeObject):
    """Note / Huomautus
    including eventual web link

    Properties:
            handle          str stats with '_' if comes from Gramps
            change          int timestamp from Gramps
            id              esim. "N0001"
            uniq_id         int database key
            priv            int >0 non-public information
            type            str note type
            text            str note description
            url             str web link
    """

    def __init__(self):
        """Creates a Note instance in memory"""
        NodeObject.__init__(self)
        self.type = ""
        self.priv = None
        self.text = ""
        self.url = None

    def __str__(self):
        desc = self.text if len(self.text) < 17 else self.text[:14] + "..."
        url = "" if self.url == None else self.url
        return "{} {} {!r} {}".format(self.id, self.type, desc, url)

    @classmethod
    def from_node(cls, node):
        """
        Transforms a db node to an object of type Note.
        """
        n = cls()
        n.uniq_id = node.id
        n.id = node["id"] or ""
        if "handle" in node:
            n.handle = node["handle"]
        n.change = node["change"]
        if "priv" in node:
            n.priv = node["priv"]
        n.type = node.get("type", "")
        n.text = node.get("text", "")
        n.url = node.get("url", "")
        return n

    # @staticmethod def get_persons_notes(uniq_id):
    # """ Read 'Person -> Event -> Note' and 'Person -> Note' paths

    # ===> removed 21.5.2021/JMä ===================================================
    #     @staticmethod
    #     def get_notes(uniq_ids):
    #         """ Reads Note nodes data from db using given Note uniq_ids
    #
    #             Called from models.datareader.get_person_data_by_id
    #         """
    #         notes = []
    #         with shareds.driver.session() as session:
    #             # """MATCH (n:Note) WHERE ID(n) in $nid RETURN ID(n) AS uniq_id, n"""
    #             result = session.run(Cypher_note.get_by_ids, nid=uniq_ids)
    #             for record in result:
    #                 # Create a Note object from record
    #                 node = record['n']
    #                 n = Note.from_node(node)
    #                 notes.append(n)
    #         return notes
    # ==============================================================================
    #     @staticmethod
    #     def get_note_list(uniq_id):
    #         """ Reads all Note nodes or selected Note node from db
    #             Also counts references to each Note
    #
    #             Called only from models.datareader.get_notes for "table_of_data.html"
    #         """
    #         result = None
    #         with shareds.driver.session() as session:
    #             if uniq_id:
    #                 query = """
    # MATCH (n:Note) WHERE ID(note)=$nid
    #     OPTIONAL MATCH (a) --> (n)
    # RETURN ID(n) AS uniq_id, n, count(a) AS ref"""
    #                 result =  session.run(query, nid=uniq_id)
    #             else:
    #                 query = """
    # MATCH (n:Note)
    #     OPTIONAL MATCH (a) --> (n)
    # RETURN ID(n) AS uniq_id, n, count(a) AS ref
    #     ORDER BY n.type"""
    #                 result =  session.run(query)
    #         titles = ['uniq_id', 'change', 'id', 'priv', 'type', 'text', 'url', 'ref']
    #         notes = []
    #         for record in result:
    #             # Create a Note object from record
    #             node = record['n']
    #             n = Note.from_node(node)
    #             n.ref = record['ref']
    #             notes.append(n)
    #         return (titles, notes)
    # ===============================================================================
    #     @staticmethod
    #     def get_total():
    #         """ Tulostaa huomautusten määrän tietokannassa """
    #
    #         with shareds.driver.session() as session:
    #             results =  session.run("MATCH (n:Note) RETURN COUNT(n)")
    #             for result in results:
    #                 return str(result[0])
    #         return 0

    @staticmethod
    def save_note_list(dataservice, **kwargs):
        """Save the parent.notes[] objects as a descendant of the parent node.

        Arguments:
            parent          NodeObject  Object to link: (parent) --> (Note)
            - parent.notes  list        Note objects
            batch_id        str         Batch id, alternative object to link:
                                        (:Batch{id:batch_id}) --> (Note)

        Called from bl.person.PersonBl.save, models.gen.repository.Repository.save
        """
        n_cnt = 0
        batch_id = kwargs.get("batch_id", None)
        parent = kwargs.get("parent", None)
        for note in parent.notes:
            if isinstance(note, Note):
                if not note.id:
                    n_cnt += 1
                    note.id = f"N{n_cnt}-{parent.id}"
                    attr = {
                        "parent_id": parent.uniq_id, 
                        "batch_id": batch_id,
                        }
                note.save(dataservice, **attr)
            else:
                raise AttributeError("note.save_note_list: Argument not a Note")

    def save(self, dataservice, **kwargs):
        """Creates this Note object as a Note node

        Arguments:
            parent_uid      uniq_id     Object to link: (parent) --> (Note)
            batch_id        str         Batch id, alternative object to link:
                                        (:Batch{id:batch_id}) --> (Note)
        """
        self.uuid = self.newUuid()
        batch_id = kwargs.get("batch_id", None)
        parent_id = kwargs.get("parent_id", None)
        if not "batch_id":
            raise RuntimeError(f"Note.save needs batch_id for {self.id}")
        n_attr = {
            "uuid": self.uuid,
            #"change": self.change,
            "id": self.id,
            "priv": self.priv,
            "type": self.type,
            "text": self.text,
            "url": self.url,
        }
        if self.handle:
            n_attr["handle"] = self.handle
        if not parent_id is None:
            #print(f"Note.save: (Root {batch_id}) --> (Note {self.id}) <-- (parent {parent_id})")
            self.uniq_id = dataservice.tx.run(
                CypherNote.create_in_batch_as_leaf,
                bid=batch_id,
                parent_id=parent_id,
                n_attr=n_attr,
            ).single()[0]
        elif not batch_id is None:
            #print(f"Note.save: (Root {batch_id}) --> (Note {self.id})")
            self.uniq_id = dataservice.tx.run(
                CypherNote.create_in_batch, 
                bid=batch_id, 
                n_attr=n_attr
            ).single()[0]
        else:
            raise RuntimeError(
                f"Note.save needs batch_id or parent_id for {self.id}"
            )


class NoteReader(DataService):
    """
    Data reading class for Note objects. Used with free text search.
    """

    def __init__(self, service_name: str, u_context=None):
        super().__init__(service_name, u_context)

    def note_search(self, args):
        context = self.user_context
        args["use_user"] = self.use_user
        args["fw"] = context.first  # From here forward
        args["limit"] = context.count
        args["batch_id"] = context.material.batch_id
        args["material_type"] = context.material.m_type
        args["state"] = context.material.state
        res = self.dataservice.tx_note_search(args)
        #print(res)
        return res
    
    