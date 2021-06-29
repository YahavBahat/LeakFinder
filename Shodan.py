from shodan import Shodan as _Shodan
from shodan import APIError
from json import load
import logging
from Logging import log_setup


class Shodan:
    log = log_setup("Shodan")

    logger = logging.getLogger("urllib3.connectionpool")
    logger.setLevel(logging.ERROR)

    def __init__(self, host, api=""):
        self.host = host
        self.api = api

        self.error = None
        self.get_api()

    def get_api(self):
        # If user didn't pass API key from the command line arguments, search in config.config file.
        if not self.api:
            with open("config.config", "r") as f:
                data = load(f)
            self.api = data.get("api")
        if not self.api:
            Shodan.log.error("You passed the --shodan/-sn api option, or defined it in config.config file,"
                             " but no Shodan API provided.")
            self.error = True

    def get_vulns(self):
        try:
            api = _Shodan(self.api)
            ip_info = api.host(self.host)
            return ip_info.get("vulns")
        except APIError as e:
            if str(e) == "Invalid API key":
                Shodan.log.error("Passed invalid Shodan API key.")
                self.error = True
