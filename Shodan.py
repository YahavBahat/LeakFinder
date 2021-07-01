from shodan import Shodan as _Shodan
from shodan import APIError
from json import load
import logging
from Logging import log_setup


class Shodan:
    log = log_setup("Shodan")

    logger = logging.getLogger("urllib3.connectionpool")
    logger.setLevel(logging.ERROR)

    def __init__(self, host=""):
        self.host = host

        self.api = None
        self.error = None
        self.cancel = None
        self.get_api()

    def get_api(self):
        # If user didn't pass API key from the command line arguments, search in config.config file.
        with open("config.config", "r") as f:
            api = load(f).get("api")
            try:
                self.api = _Shodan(api)
            except APIError as e:
                if str(e) == "Invalid API key":
                    Shodan.log.error("Passed invalid Shodan API key.")
                    self.error = True
        if not self.api:
            self.cancel, self.error = True, True

    def get_hostnames(self):
        try:
            ip_info = self.api.host(self.host)
            return ip_info.get("hostnames")
        except APIError as e:
            if str(e) == "Invalid API key":
                Shodan.log.error("Passed invalid Shodan API key.")
                self.error = True

    def get_vulns(self):
        try:
            ip_info = self.api.host(self.host)
            return ip_info.get("vulns")
        except APIError as e:
            if str(e) == "Invalid API key":
                Shodan.log.error("Passed invalid Shodan API key.")
                self.error = True

    def stream(self):
        try:
            for banner in self.api.stream.ports([3306, 27017, 9200, 9042]):
                host, port = banner.get("ip_str"), banner.get("port")
                yield host, port
        except Exception as e:
            Shodan.log.error(f"Shodan Stream: SOMETHING WENT WRONG.\n{e}\n")
