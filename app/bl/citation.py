"""
    Citation class for handling Citation nodes and relations and
    NodeRef class to store data of referring nodes and Source

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
"""

# blacked 25.5.2021/JMä
from sys import stderr
import logging
from bl.dates import DateRange

logger = logging.getLogger("stkserver")

# import shareds
from bl.base import NodeObject
from pe.neo4j.cypher.cy_citation import CypherCitation
#from models.cypher_gramps import Cypher_citation_w_handle
# from .cypher import Cypher_citation


class Citation(NodeObject):
    """Lähdeviittaus

    Properties:
            handle           str
            change           int
            id               esim. "C0001"
            dates            DateRange date
            page             str page description
            confidence       str confidence 0.0 - 5.0 (?)
            note_ref         int huomautuksen osoite (ent. note_handles str)
            source_handle    str handle of source   _or_
            source_id        int uniq_id of a Source object
            citators         NodeRef nodes referring this citation
    """

    def __init__(self):
        """ Creates a Citation instance """

        NodeObject.__init__(self)
        self.dates = None
        self.page = ""
        self.confidence = ""
        self.mark = ""  # citation mark display references
        self.mark_sorter = 0  # citation grouping by source variable

        self.note_handles = []  # Gramps handle
        self.source_handle = ""

        # For displaying citations in person.html
        self.source_id = None

        self.citators = []  # Lähde-sivulle
        self.note_ref = []

    def __str__(self):
        return f"{self.mark} {self.id} '{self.page}'"

    @classmethod
    def from_node(cls, node):
        """
        Transforms a db node to an object of type Citation.
        """
        n = cls()
        n.uniq_id = node.id
        if "handle" in node:
            n.handle = node["handle"]
        n.change = node["change"]
        n.id = node["id"]
        n.uuid = node["uuid"]
        n.confidence = node["confidence"]
        n.page = node["page"]
        n.dates = DateRange.from_node(node)

        return n

    #     @staticmethod  def get_persons_citations (uniq_id):
    #         """ Read 'Person -> Event -> Citation' and 'Person -> Citation' paths

    # ==== removed 25.5.2021/JMä ===================================================
    #     @staticmethod
    #     def get_source_repo (uniq_id=None):
    #         """ Read Citation -> Source -> Repositories chain
    #             and optionally Notes.
    #             Citation has all data but c.handle
    #
    #             Voidaan lukea annetun Citationin lähde ja arkisto kannasta
    #         """
    #         with shareds.driver.session() as session:
    #             if uniq_id:
    #                 return session.run(Cypher_citation.get_cita_sour_repo,
    #                                    uid=uniq_id)
    #             else:
    #                 return session.run(Cypher_citation.get_cita_sour_repo_all)
    #
    #     def get_sourceref_hlink(self):
    #         """ Voidaan lukea lähdeviittauksen lähteen uniq_id kannasta
    #         """
    #         query = """
    #  MATCH (citation:Citation)-[r:SOURCE]->(source:Source) WHERE ID(citation)={}
    #  RETURN ID(source) AS id
    #  """.format(self.uniq_id)
    #         result = shareds.driver.session().run(query)
    #         for record in result:
    #             if record['id']:
    #                 self.source_handle = record['id']
    #
    #     @staticmethod
    #     def get_total():
    #         """ Tulostaa lähteiden määrän tietokannassa """
    #         query = """
    #             MATCH (c:Citation) RETURN COUNT(c)
    #             """
    #         results = shareds.driver.session().run(query)
    #         for result in results:
    #             return str(result[0])
    #
    #     def print_data(self):
    #         """ Tulostaa tiedot """
    #         print ("*****Citation*****")
    #         print ("Handle: " + self.handle)
    #         print ("Change: {}".format(self.change))
    #         print ("Id: " + self.id)
    #         print ("Dates: " + self.dates)
    #         print ("Page: " + self.page)
    #         print ("Confidence: " + self.confidence)
    #         if len(self.note_handles) > 0:
    #             for i in range(len(self.note_handles)):
    #                 print ("Noteref_hlink: " + self.note_handles[i])
    #         if self.source_handle != '':
    #             print ("Sourceref_hlink: " + self.source_handle)
    #         return True

    def save(self, tx, **kwargs):
        """Saves this Citation and connects it to it's Notes and Sources."""
        if "batch_id" in kwargs:
            batch_id = kwargs["batch_id"]
        else:
            raise RuntimeError(f"Citation_gramps.save needs batch_id for {self.id}")

        self.uuid = self.newUuid()
        c_attr = {}
        try:
            c_attr = {
                "uuid": self.uuid,
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "page": self.page,
                "confidence": self.confidence,
            }
            if self.dates:
                c_attr.update(self.dates.for_db())

            result = tx.run(
                CypherCitation.create_to_batch,
                batch_id=batch_id,
                c_attr=c_attr,
            )
            ids = []
            for record in result:
                self.uniq_id = record[0]
                ids.append(self.uniq_id)
                if len(ids) > 1:
                    print(
                        "iError updated multiple Citations {} - {}, attr={}".format(
                            self.id, ids, c_attr
                        )
                    )
        except Exception as err:
            print("iError: Event_save: {0} attr={1}".format(err, c_attr), file=stderr)
            raise RuntimeError("Could not save Citation {}".format(self.id))

        # Make relations to the Note nodes
        try:
            for handle in self.note_handles:
                tx.run(
                    CypherCitation.link_note, handle=self.handle, hlink=handle
                )
        except Exception as err:
            logger.error(
                f"Citation.save: {err} in linking Notes {self.handle} -> {self.note_handles}"
            )
            print(
                "iError: Citation.save Note hlink: {0} {1}".format(err, self.id),
                file=stderr,
            )

        try:
            # Make relation to the Source node
            if self.source_handle != "":
                tx.run(
                    Cypher_citation_w_handle.link_source,
                    handle=self.handle,
                    hlink=self.source_handle,
                )
        except Exception as err:
            print(
                "iError: Citation.save Source hlink: {0} {1}".format(err, self.id),
                file=stderr,
            )

        return


# ==== removed 25.5.2021/JMä ===================================================
# class NodeRef():
#     ''' Carries data of citating objects.
#
#         Used only in models.datareader.get_source_with_events
#
#             label            str (optional) Person or Event
#             uniq_id          int Persons uniq_id
#             source_id        int The uniq_id of the Source citated
#             clearname        str Persons display name
#             eventtype        str type for Event
#             edates           DateRange date expression for Event
#             date             str date for Event
#
#         Used in from models.datareader.get_source_with_events
#         and scene/source_events.html
#
#         TODO Plan
#             (b:baseObject) --> (a:activeObject) --> (c:Citation)
#             b.type=Person|Family     for linking object page
#             a.type=Person|Event|Name for display style
#             c                        to display
#                 + remove: self.date
#     '''
#     def __init__(self):
#         self.label = ''
#         self.uniq_id = ''
#         self.source_id = None
#         self.clearname = ''
#         self.eventtype = ''
#         self.edates = None
#         self.date = ''
#
#     def __str__(self):
#         return "{} {}: {} {} '{}'".format(self.label, self.uniq_id, self.source_id or '-', self.eventtype, self.clearname)
