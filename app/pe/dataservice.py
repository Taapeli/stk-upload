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
    """Public methods for accessing active database.
    The current database is defined in /setups.py.
    """

    def __init__(self, service_name: str, user_context=None, tx=None):
        """Create a reader object with db driver and user context.

        :param: service_name    str - one of service names (update, read, read_tx, simple)
        :param: user_context    <ui.user_context.UserContext object>
        :param: tx              <neo4j.work.transaction.Transaction object>

        - 1. if tx is given                              Use preset transaction
        - 2. if service_name is 'update' or 'read_tx'    Create transaction
        - 3. else                                        No transaction
        """
        self.idstr = f"{self.__class__.__name__}>DataService"
        print(f'#~~~{self.idstr} init')
        # Find <class 'pe.neo4j.*service'> and initilialize it
        self.service_name = service_name
        service_class = shareds.dataservices.get(self.service_name)
        if not service_class:
            raise KeyError(
                f"pe.dataservice.DataService.__init__: name {self.service_name} not found"
            )
        self.dataservice = service_class(shareds.driver)
        self.pre_tx = tx
        # Prepare to restore the privious dataservice, if one exists
        if shareds.dservice:
            self.previous_dservice = shareds.dservice
        else:
            self.previous_dservice = None
        shareds.dservice = self.dataservice

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
        if self.pre_tx:
            # 1. Use given transaction
            print(f'#~~~{self.idstr} enter active {self.pre_tx}')
            self.dataservice.tx = self.pre_tx
        else:
            if self.service_name == "update" or self.service_name == "read_tx":
                # 2. Create transaction
                self.dataservice.tx = shareds.driver.session().begin_transaction()
                print(f'#~~~{self.idstr} enter "{self.service_name}" transaction') # {self.pre_tx}')

            else:
                # 3. No transaction
                self.dataservice.tx = None
                print(f'#~~~{self.idstr} enter') # {self.pre_tx}')
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
        #print(f"--{self.idstr} exit {self.dataservice.tx} prev {self.pre_tx}")
        if self.dataservice.tx:
            if exc_type:
                e = exc_type.__class__.__name__
                print(f"--{self.idstr} exit rollback {e}")
                self.dataservice.tx.rollback()
            else:
                if self.pre_tx is None:
                    print(f'#~~~{self.idstr} exit commit')
                    self.dataservice.tx.commit()
                else:
                    print(f'#~~~{self.idstr} exit continue')
        else:
            print(f'#~~~{self.idstr} exit')

        if self.previous_dservice:
            shareds.dservice = self.previous_dservice
            print(f"--{self.idstr} {shareds.dservice} replaced by {self.previous_dservice}")
            self.previous_dservice = None
        else:
            shareds.dservice = None


class ConcreteService:
    """Base class for all concrete database service classes.
    """
    pass

