from cassandra.cluster import Cluster, ExecutionProfile
from cassandra.policies import WhiteListRoundRobinPolicy
import logging
from Logging import log_setup


class Cassandra:
    log = log_setup("Cassandra")

    logger = logging.getLogger('cassandra')
    logger.setLevel(logging.ERROR)
    logger.disabled = True

    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.profile = ExecutionProfile(
            load_balancing_policy=WhiteListRoundRobinPolicy(['127.0.0.1'])
        )
        self.cluster = None
        self.session = None
        self.database_names_gen = None
        self.collections_names_gen_list = []
        self.cluster_size = -1

        self.connect()

    def connect(self):
        try:
            self.cluster = Cluster([self.host], port=self.port, execution_profiles=
            {"EXEC_PROFILE_DEFAULT": self.profile})
            self.session = self.cluster.connect()
        except Exception:
            Cassandra.log.info(f"Couldn't establish connection for {self.host}\n")

    def list_database_names(self):
        self.database_names_gen = (keyspace.keyspace_name for keyspace in self.session.execute(
            "SELECT keyspace_name FROM system_schema.keyspaces;") if keyspace.keyspace_name not in
                                   ["system", "system_distributed", "system_auth", "system_traces", "system_schema"])

    def list_collections_names(self):
        for database in self.database_names_gen:
            self.collections_names_gen_list = (table.table_name for table in self.session.execute(
                f"SELECT * FROM system_schema.tables WHERE keyspace_name = '{database}';"))

    def get_total_size(self):
        pass
