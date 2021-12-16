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
'''
Created on 7.12.2021

@author: jm
'''

import shareds
import logging
#from bl.base import IsotammiException
from pe.neo4j.updateservice import Neo4jUpdateService

logger = logging.getLogger('stkserver')

def obj_addr(tx):
    "Returns obj address for debug, for ex. '0x7fc585350fd0'"
    return str(tx).split(" ", 3)[-1][:-1] if tx else 'None'


class ManagedDataService(Neo4jUpdateService):
    """Public methods for accessing active database using managed write transactions.
    The current database is defined in /setups.py.

    Follows Context Manager pattern allowing automatic transaction management
    by 'with' statement.

    (Developed from pe.dataservice.DataService by removing transaction.)
    
    @See https://docs.python.org/3/reference/datamodel.html#with-statement-context-managers
    @see: https://neo4j.com/docs/api/python-driver/current/api.html#transaction
    
    @change: Do not create here a transaction for 'update' service. / 7.12.2021 JMä
    """

    def __init__(self, service_name: str, user_context=None, tx=None):
        """Create a reader object with db driver and user context.

        :param: service_name    str - one of service names ('update', 'read', 'read_tx', 'simple')
        :param: user_context    <ui.context.UserContext object>
        :param: tx              None or <neo4j.work.transaction.Transaction object>

        - 1. if tx is given                  Use the given, opened transaction
        - 2. else                            No transaction
        """
        txstr = "+tx" if tx else ""
        self.idstr = f"{self.__class__.__name__}>ManagedDataService{txstr}"
        logger.debug(f'#~~~{self.idstr} init')
        # Find <class 'pe.neo4j.*service'> and initialize it
        self.service_name = service_name
        service_class = shareds.dataservices.get(self.service_name)
        if not service_class:
            raise KeyError(
                f"pe.dataservice.ManagedDataService.__init__: name {self.service_name} not found"
            )
        # Initiate selected service object
        self.dataservice = service_class(shareds.driver)
        self.given_tx = tx

        if user_context:
            self.user_context = user_context
            self.username = user_context.user
            # The operative username
            if user_context.is_common():
                self.use_user = None
            else:
                self.use_user = user_context.user
        else:
            #raise IsotammiException("pe.dataservice.DataService: user_context is mandatory")
            pass

    def __enter__(self):
        # With 'update' and 'read_tx' begin transaction
        if self.given_tx:
            # 1. Use given transaction
            logger.debug(f'#~~~{self.idstr} enter active tx={obj_addr(self.given_tx)}')
            self.dataservice.tx = self.given_tx
        else:
            # 2. No transaction in this level
            self.dataservice.tx = None
            logger.debug(f'#~~~{self.idstr} enter') # {obj_addr(self.given_tx)}')
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """Exit the runtime context related to this object.

        The parameters describe the exception that caused the context to be
        exited. If the context was exited without an exception, all three
        arguments will be None.
        """
        #logger.debug(f"--{self.idstr} exit tx={obj_addr(self.dataservice.tx)} prev {obj_addr(self.given_tx)}")
        if self.dataservice.tx:
            if exc_type:
                logger.info(f"--{self.idstr} exit rollback {exc_type}")
                if self.given_tx is None:
                    self.dataservice.tx.rollback()
            else:
                if self.given_tx is None:
                    logger.info(f'#~~~{self.idstr} exit commit tx={obj_addr(self.dataservice.tx)}')
                    try:
                        self.dataservice.tx.commit()
                    except Exception as e:
                        logger.error(f'#~~~{self.idstr} exit commit FAILED, {e.__class__.__name__} {e}')
                else:
                    logger.info(f'#~~~{self.idstr} exit continue tx={obj_addr(self.dataservice.tx)}')
        else:
            logger.info(f'#~~~{self.idstr} exit {obj_addr(self.given_tx)}')


# class ConcreteService:
#     "Base class for all concrete database service classes."
#     pass
