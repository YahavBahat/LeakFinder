from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError
from Logging import log_setup


# TODO: add option to try to connect with default password
# TODO: catch errors in all the class methods
class MongoDB:
    log = log_setup(__name__)

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.client = None
        self.database_names_gen = None
        self.collections_names_gen_list = []
        self.cluster_size = 0

        self.connect()

    def connect(self):
        try:
            self.client = MongoClient(self.host, self.port)
        except Exception:
            MongoDB.log.info(f"Couldn't establish connection for {self.host}\n")

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
