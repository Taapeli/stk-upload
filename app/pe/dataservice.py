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

import shareds
import logging 
logger = logging.getLogger('stkserver')


class DataService:
    ''' Public methods for accessing active database.
    
        Returns a PersonResult object
    '''
    def __init__(self, service_name:str, user_context=None):
        ''' Create a reader object with db driver and user context.

            :param: service_name    str - one of service names (update, read, read_tx)
            :param: user_context    <ui.user_context.UserContext object>

            A new transaction is created for 'update' and 'read_tx' services
        '''
        # Find <class 'pe.neo4j.*service'> and initilialize it
        self.service_name = service_name
        service_class = shareds.dataservices.get(self.service_name)
        if not service_class:
            raise KeyError(f"pe.dataservice.DataService.__init__: name {self.service_name} not found")
        self.dataservice = service_class(shareds.driver)
        
        if user_context:
            self.user_context = user_context
            self.username = user_context.user
            # The operative username
            if user_context.context == user_context.ChoicesOfView.COMMON:
                self.use_user = None
            else:
                self.use_user = user_context.user

    def __enter__(self):
        # With 'update' and 'read_tx' begin transaction
        if self.service_name == "update" or self.service_name == "read_tx":
            self.dataservice.tx = shareds.driver.session().begin_transaction()
            print(f'#{self.__class__.__name__} {self.service_name} begin')
        else:
            print(f'#{self.__class__.__name__} enter')
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """
        Exit the runtime context related to this object. 

        @See https://docs.python.org/3/reference/datamodel.html#with-statement-context-managers

        object.__exit__(self, exc_type, exc_value, traceback)
        The parameters describe the exception that caused the context to be 
        exited. If the context was exited without an exception, all three
        arguments will be None.
        """
        if self.dataservice.tx:
            if exc_type:
                print(f"{self.__class__.__name__} rollback becouse of {exc_type.__class__.__name__}")
                self.dataservice.tx.rollback()
            else:
                self.dataservice.tx.close()
            print(f'#{self.__class__.__name__} exit')

#===============================================================================
#     # -------- Person methods --------
# 
#     def get_person_search(self, args):
#         """ Read Persons with Names, Events, Refnames (reference names) and Places
#             and Researcher's username.
#         
#             Search by name by args['rule'], args['key']:
#                 rule=all                  all
#                 rule=surname, key=name    by start of surname
#                 rule=firstname, key=name  by start of the first of first names
#                 rule=patronyme, key=name  by start of patronyme name
#                 rule=refname, key=name    by exact refname
#                 rule=years, key=str       by possible living years:
#                     str='-y2'   untill year
#                     str='y1'    single year
#                     str='y1-y2' year range
#                     str='y1-'   from year
# 
#             Origin from bl.person.PersonReader.get_person_search
#             TODO: rule=refname: listing with refnames not supported
#         """
#         if args.get('rule') == 'years':
#             try:
#                 lim = args['key'].split('-')
#                 y1 = int(lim[0]) if lim[0] > '' else -9999
#                 y2 = int(lim[-1]) if lim[-1] > '' else 9999
#                 if y1 > y2:
#                     y2, y1 = [y1, y2]
#                 args['years'] = [y1, y2]
#             except ValueError:
#                 return {'statustext':_('The year or years must be numeric'), 'status': Status.ERROR}
# 
# #         planned_search = {'rule':args.get('rule'), 'key':args.get('key'), 
# #                           'years':args.get('years')}
# 
#         context = self.user_context
#         args['use_user'] = self.use_user
#         args['fw'] = context.first  # From here forward
#         args['limit'] = context.count
#         
#         res = self.dataservice.tx_get_person_list(args)
# 
#         status = res.get('status')
#         if status == Status.NOT_FOUND:
#             msg = res.get("statustext")
#             logger.error(f'bl.person.PersonReader.get_person_search: {msg}')
#             print(f'bl.person.PersonReader.get_person_search: {msg}')
#             return {'items':[], 'status':res.get('status'),
#                     'statustext': _('No persons found')}
#         if status != Status.OK:
#             return res
#         persons = []
# 
#         # got {'items': [PersonRecord], 'status': Status.OK}
#         #    - PersonRecord = object with fields person_node, names, events_w_role, owners
#         #    -    events_w_role = list of tuples (event_node, place_name, role)
#         for p_record in res.get('items'):
#             #print(p_record)
#             node = p_record.person_node
#             p = PersonBl.from_node(node)
# 
#             # if take_refnames and record['refnames']:
#             #     refnlist = sorted(record['refnames'])
#             #     p.refnames = ", ".join(refnlist)
# 
#             for node in p_record.names:
#                 pname = Name.from_node(node)
#                 pname.initial = pname.surname[0] if pname.surname else ''
#                 p.names.append(pname)
# 
#             # Events 
#             for node, pname, role in p_record.events_w_role:
#                 if not node is None:
#                     e = EventBl.from_node(node)
#                     e.place = pname or ""
#                     if role and role != "Primary":
#                         e.role = role
#                     p.events.append(e)
#     
#             persons.append(p)   
#     
#         # Update the page scope according to items really found
#         if len(persons) > 0:
#             context.update_session_scope('person_scope', 
#                                           persons[0].sortname, persons[-1].sortname, 
#                                           context.count, len(persons))
# 
#         if self.use_user is None:
#             persons2 = [p for p in persons if not p.too_new]
#             num_hidden = len(persons) - len(persons2)
#         else:
#             persons2 = persons
#             num_hidden = 0
#         return {'items': persons2, 'num_hidden': num_hidden, 'status': status}
#===============================================================================


