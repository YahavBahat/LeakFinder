from mysql.connector import (connection)
from mysql.connector import Error as MySQLError
from mysql.connector import errorcode
import logging
from Logging import log_setup, no_connection


# TODO: remove parameters user and password and add option to try to connect with default password
class MySQL:
    log = log_setup("MySQL")

    logger = logging.getLogger('mysql')
    logger.setLevel(logging.CRITICAL)
    logger.disabled = True

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.error = None
        self.cnx = None
        self.cursor = None
        self.database_names_gen = None
        self.collections_names_gen_list = []
        self.cluster_size = 0
        self.credentials = {}
        self.default_logins = {"root": "", "root": "root"}

        self.connect()

    def connect(self, user="", password=""):
        try:
            self.cnx = connection.MySQLConnection(host=self.host, port=self.port, user=user, password=password)
            self.cursor = self.cnx.cursor(buffered=True)
            self.credentials[user] = password
        except MySQLError as e:
            if e.errno == errorcode.ER_ACCESS_DENIED_ERROR and user != list(self.default_logins.keys())[-1] \
                    and password != list(self.default_logins.values())[-1]:
                # Try default password based on passed option
                for _user, _password in self.default_logins.items():
                    self.connect(user=_user, password=_password)
            else:
                MySQL.log.info(no_connection(self.host))
                self.error = True

    def list_database_names(self):
        self.cursor.execute("SHOW DATABASES;")
        self.database_names_gen = (database[0] for database in self.cursor if database[0] not in ["information_schema",
                                                                                                  "performance_schema",
                                                                                                  "sys", "mysql"])

    def list_collections_names(self):
        for database in self.database_names_gen:
            try:
                for index, gen in enumerate(self.cursor.execute(f"USE {database}; SHOW TABLES;", multi=True)):
                    if index == 1:
                        for table in gen:
                            self.collections_names_gen_list.append(table[0])
            except Exception:
                pass

    def get_total_size(self):
        # In bytes
        query = """
        SELECT table_schema AS "DB_NAME", 
        sum( data_length + index_length ) 
        FROM information_schema.TABLES GROUP BY table_schema ;
        """
        self.list_database_names()
        for database in self.database_names_gen:
            for index, gen in enumerate(self.cursor.execute(query.replace("DB_NAME", database), multi=True)):
                if index == 0:
                    for table in gen:
                        self.cluster_size += int(table[-1])
