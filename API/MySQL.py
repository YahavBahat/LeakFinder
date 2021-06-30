from mysql.connector import (connection)
from mysql.connector import Error as MySQLError
from mysql.connector import errorcode
from Logging import no_connection
import logging
from Logging import log_setup


# TODO: remove parameters user and password and add option to try to connect with default password
class MySQL:
    log = log_setup("MySQL")

    logging.getLogger('mysql.connector').setLevel(logging.CRITICAL)
    logging.getLogger('mysql').setLevel(logging.CRITICAL)

    def __init__(self, host, port, try_default):
        self.host = host
        self.port = port
        self.try_default = try_default

        self.authentication_failed = None
        self.error = None
        self.cnx = None
        self.cursor = None
        self.database_names_gen = None
        self.collections_names_gen_list = []
        self.cluster_size = 0
        self.login_credentials = {}
        self.default_login = (("root", ""), ("root", "root"))

        self.connect()

    def retry(self, user, password):
        try:
            self.cnx = connection.MySQLConnection(host=self.host, port=self.port, user=user, password=password)
            self.cursor = self.cnx.cursor(buffered=True)
            self.authentication_failed = False

        except MySQLError as e:
            if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                self.authentication_failed = True

            else:
                self.error = True

    def connect(self):
        try:
            self.cnx = connection.MySQLConnection(host=self.host, port=self.port, user="", password="")
            self.cursor = self.cnx.cursor(buffered=True)
            self.authentication_failed = False
        except MySQLError as e:
            if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                self.authentication_failed = True

                if self.try_default:
                    for tries_count, login_tuple in enumerate(self.default_login):
                        user, password = login_tuple
                        self.retry(user, password)
                        if not self.authentication_failed:
                            self.login_credentials["user"] = user
                            self.login_credentials["password"] = password

            else:
                self.error = True
            no_connection(self.host)

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
