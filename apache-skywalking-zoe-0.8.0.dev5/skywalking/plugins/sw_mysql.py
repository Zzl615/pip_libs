#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from skywalking import Layer, Component, config
from skywalking.trace.context import get_context
from skywalking.trace.tags import TagDbType, TagDbInstance, TagDbStatement, TagDbSqlParameters

link_vector = ['mysql-connector']
support_matrix = {
    'mysql': {
        '>=3.6': ['1.0']
    }
}
note = """"""


def install():
    from mysql.connector.connection import MySQLCursor

    _execute = MySQLCursor.execute

    def _sw_execute(this: MySQLCursor, operation, params=None, multi=False):
        try:
            peer = f'{this._connection._host}:{this._connection._port}'

            context = get_context()
            with context.new_exit_span(op='Mysql/MysqlConnector/execute', peer=peer,
                                       component=Component.PyMysql) as span:
                span.layer = Layer.Database
                res = _execute(this, operation, params, multi)

                span.tag(TagDbType('mysql'))
                span.tag(TagDbInstance(this._connection._database))
                span.tag(TagDbStatement(operation))

                if config.sql_parameters_length and params:
                    if isinstance(params, list):
                        parameter = ','.join([str(arg) for arg in params])
                    elif isinstance(params, dict):
                        parameter = ','.join([f'{k}:{v}' for k, v in params.items()])
                    max_len = config.sql_parameters_length
                    parameter = f'{parameter[0:max_len]}...' if len(parameter) > max_len else parameter
                    span.tag(TagDbSqlParameters(f'[{parameter}]'))

                return res
        except Exception as e:
            res = _execute(this, operation, params, multi)
            return res

    MySQLCursor.execute = _sw_execute
