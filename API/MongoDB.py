from pymongo import MongoClient
from pymongo.database import Database
import logging
from Logging import log_setup, no_connection


# TODO: add option to try to connect with default password
# TODO: catch errors in all the class methods
class MongoDB:
    log = log_setup("MongoDB")

    logger = logging.getLogger('pymongo')
    logger.setLevel(logging.CRITICAL)

    def __init__(self, host, port, try_default):
        self.host = host
        self.port = port
        self.try_default = try_default

        self.error = None
        self.client = None
        self.database_names_gen = None
        self.collections_names_gen_list = []
        self.cluster_size = 0

        self.connect()

    def connect(self):
        try:
            self.client = MongoClient(self.host, self.port)
        except Exception:
            MongoDB.log.info(no_connection(self.host))
            self.error = True

    def list_database_names(self):
        self.database_names_gen = (database["name"] for database in self.client.list_databases())

    def list_collections_names(self):
        for database in self.database_names_gen:
            self.collections_names_gen_list.extend((collection["name"] for collection in
                                                    Database(self.client, database).list_collections()))

    def get_total_size(self):
        # In bytes
        for database in self.client.list_databases():
            self.cluster_size += database["sizeOnDisk"]
