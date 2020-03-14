'''
Created on 12.3.2020

@author: jm
'''
import shareds
from pe.neo4j.place_cypher import CypherPlace

def _read_place_list(o_context):
    """ Read Place data from given fw 
    """
    # Select a) filter by user b) show Isotammi common data (too)
    show_by_owner = o_context.use_owner_filter()
    show_with_common = o_context.use_common()
    user = o_context.user
    fw = o_context.next_name_fw()     # next name
    try:
        """
                       show_by_owner    show_all
                    +-------------------------------
        with common |  me + common      common
        no common   |  me                -
        """
        with shareds.driver.session() as session:
            if show_by_owner:

                if show_with_common: 
                    #1 get all with owner name for all
                    print("_read_place_list: by owner with common")
                    result = session.run(CypherPlace.get_name_hierarchies,
                                         user=user, fw=fw, limit=o_context.count)

                else: 
                    #2 get my own (no owner name needed)
                    print("_read_place_list: by owner only")
                    result = session.run(CypherPlace.get_my_name_hierarchies,
                                         user=user, fw=fw, limit=o_context.count)

            else: 
                #3 == #1 simulates common by reading all
                print("_read_place_list: common only")
                result = session.run(CypherPlace.get_name_hierarchies, #user=user, 
                                     fw=fw, limit=o_context.count)
                
            return result
    except Exception as e:
        print('Error _read_person_list: {} {}'.format(e.__class__.__name__, e))            
        raise      

