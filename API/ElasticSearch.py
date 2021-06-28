from elasticsearch import Elasticsearch
import logging
from Logging import log_setup


# TODO: catch errors in all the class methods
class ElasticSearch:
    log = log_setup(__name__)

    # Disable elasticsearch logging
    logger = logging.getLogger('elasticsearch')
    logger.disabled = True

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.es = None
        self.cluster_size = 0
        self.database_names_gen = None
        self.collections_names_gen_list = iter(())

        self.connect()

    def connect(self):
        self.es = Elasticsearch(f"{self.host}:{self.port}")
        if not self.es.ping():
            ElasticSearch.log.info(f"Couldn't establish connection for {self.host}\n")

    def list_database_names(self):
        self.database_names_gen = iter(self.es.indices.get_alias().keys())

    def list_collections_names(self):
        pass

    def get_total_size(self):
        # In bytes
        for json in self.es.cat.indices(format="json", bytes="b"):
            self.cluster_size += int(json["pri.store.size"])
