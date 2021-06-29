from cassandra.cluster import Cluster, ExecutionProfile
from cassandra.policies import WhiteListRoundRobinPolicy, ExponentialReconnectionPolicy
from cassandra import AuthenticationFailed, ConsistencyLevel
from cassandra.auth import PlainTextAuthProvider
import logging
from Logging import log_setup


class Cassandra:
    log = log_setup("Cassandra")

    logging.getLogger('cassandra').setLevel(logging.CRITICAL)

    def __init__(self, host, port, try_default):
        self.host = host
        self.port = port
        self.try_default = try_default

        self.authentication_failed = None
        self.error = None
        self.profile = ExecutionProfile(
            load_balancing_policy=WhiteListRoundRobinPolicy(['127.0.0.1']),
            retry_policy=ExponentialReconnectionPolicy(4, 50),
            consistency_level=ConsistencyLevel.LOCAL_ONE,
            request_timeout=40,
            serial_consistency_level=ConsistencyLevel.LOCAL_SERIAL
        )
        self.cluster = None
        self.session = None
        self.database_names_gen = None
        self.collections_names_gen_list = []
        self.cluster_size = -1
        self.login_credentials = {}
        self.default_login = (("cassandra", "cassandra"))

        self.connect()

    def retry(self, user, password):
        try:
            self.cluster = Cluster([self.host], port=self.port,
                                   execution_profiles={"EXEC_PROFILE_DEFAULT": self.profile},
                                   auth_provider=PlainTextAuthProvider(username=user, password=password))
            self.session = self.cluster.connect()
            self.authentication_failed = False

        except AuthenticationFailed:
            self.authentication_failed = True

        except Exception:
            self.error = True

    def connect(self):
        try:
            self.cluster = Cluster([self.host], port=self.port,
                                   execution_profiles={"EXEC_PROFILE_DEFAULT": self.profile},
                                   auth_provider=PlainTextAuthProvider(username="", password=""))
            self.session = self.cluster.connect()
            self.authentication_failed = False

        except AuthenticationFailed:
            self.authentication_failed = True

            if self.try_default:
                for tries_count, login_tuple in enumerate(self.default_login):
                    user, password = login_tuple
                    self.retry(user, password)
                    if not self.authentication_failed:
                        self.login_credentials["user"] = user
                        self.login_credentials["password"] = password

        except Exception:
            self.error = True

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
