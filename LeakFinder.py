import click
from cloup import command, option, option_group
from cloup.constraints import mutually_exclusive
from importlib import import_module
from Output import Output, valid_file
from Filter import Filter
from datetime import datetime
from Logging import log_setup
from concurrent.futures import ProcessPoolExecutor
from Shodan import Shodan
import nmap3
from urllib3.exceptions import ProtocolError
from requests.exceptions import ChunkedEncodingError
from http.client import IncompleteRead


def return_matched_against(matched_against_dict):
    return [key.replace("_", " ").title() for key, value in matched_against_dict.items() if value]


class LeakFinder:
    log = log_setup("LeakFinder")
    cluster_ip = {"3306": "MySQL", "27017": "MongoDB", "9200": "ElasticSearch", "9042": "Cassandra"}
    filename = datetime.now().strftime("%m.%d.%Y %H:%M:%S")
    nmap = nmap3.Nmap()

    def __init__(self, hosts_file, shodan_stream, version_scan, patterns, match_against, size, output, format_,
                 exclude_unmatched, include_geo, processes, try_default, shodan_vulns, silent):
        self.hosts_file = hosts_file
        self.shodan_stream = shodan_stream
        self.version_scan = version_scan
        self.patterns = patterns
        self.match_against = match_against
        self.size = size
        self.output = output
        self.format_ = format_
        self.exclude_unmatched = exclude_unmatched
        self.include_geo = include_geo
        self.processes = processes
        self.try_default = try_default
        self.shodan_vulns = shodan_vulns
        self.silent = silent

        self.host, self.port = None, None
        self.cluster_instance, self.filter_instance = None, None
        # self.module_name = None

    def yieldConnectionTuple(self):
        if self.hosts_file:
            with open(self.hosts_file, "r") as f:
                for line in f:
                    line = line.strip().split(":")
                    yield line
        elif self.shodan_stream:
            s = Shodan()
            yield from s.stream()

    def get_service(self):
        try:
            return LeakFinder.nmap.scan_top_ports(self.host, args=f"-sV -Pn -p {self.port}").get(self.host).get("ports")[0].get("service").get("product")
        except Exception:
            pass

    def get_cluster_object(self):
        module_name = LeakFinder.cluster_ip.get(str(self.port))
        if not module_name:
            if self.version_scan:
                LeakFinder.log.warning(f"Port {self.port} is not linked with any module. Trying NMAP service scan...")
                module_name = [module_name for module_name in LeakFinder.cluster_ip.values() if
                               module_name.lower() in self.get_service().lower()]
                if module_name:
                    module_name = module_name[-1]
                else:
                    LeakFinder.log.warning(
                        f"Port {self.port} is not linked with any module. Available modules by host ports "
                        f"\n{LeakFinder.cluster_ip}"
                    )
            else:
                LeakFinder.log.warning(
                    f"Port {self.port} is not linked with any module. Available modules by host ports "
                    f"\n{LeakFinder.cluster_ip}")
        module = import_module(f"API.{module_name}")
        return getattr(module, module_name), module_name

    def cluster_method_manager(self):
        if self.patterns:
            if self.match_against == "Databases names":
                self.cluster_instance.list_database_names()
            elif self.match_against == "Documents names":
                self.cluster_instance.list_collections_names()
            else:
                self.cluster_instance.list_database_names()
                self.cluster_instance.list_collections_names()
        self.cluster_instance.get_total_size()

    # Returns a dictionary for class Output
    def info_builder(self, module_name):
        s = Shodan(self.host)

        info = {"host": self.host, "port": self.port}

        hostnames = s.get_hostnames()

        if hostnames:
            info["hostnames"] = hostnames

        info.update({"cluster_size": self.cluster_instance.cluster_size,
                     "module": module_name})

        if self.filter_instance.pattern_match:
            info["matches"] = self.filter_instance.matches
        info["matched_against"] = return_matched_against({"regex_match": self.filter_instance.pattern_match,
                                                          "size_match": self.filter_instance.size_match})

        if module_name in ("Cassandra", "MySQL") and self.cluster_instance.login_credentials:
            info["login_credentials"] = str(self.cluster_instance.login_credentials).replace("{", "").replace("}", "")

        if (any((self.filter_instance.size_match, self.filter_instance.pattern_match))
                and self.shodan_vulns and not any((s.error, s.cancel))):
            vulns = s.get_vulns()
            if vulns:
                info["vulnerabilities"] = vulns
        return info

    def main(self, connection_tuple):
        self.host, self.port = connection_tuple

        self.port = str(self.port)

        cluster_obj, module_name = self.get_cluster_object()

        self.cluster_instance = cluster_obj(self.host, self.port, self.try_default)

        if not self.cluster_instance.error:
            self.cluster_method_manager()
            self.filter_instance = Filter(self.cluster_instance, self.patterns, self.match_against, self.size)

            if not self.exclude_unmatched or any(
                    (self.filter_instance.pattern_match, self.filter_instance.size_match)
            ):

                Output(self.info_builder(module_name), f"OUTPUT {LeakFinder.filename}", self.output, self.format_,
                       self.exclude_unmatched, self.include_geo, self.silent)

    def wrapper(self):
        if self.hosts_file:
            valid_file(self.hosts_file, "hosts_file", LeakFinder.log)
        if self.patterns:
            valid_file(self.patterns, "patterns", LeakFinder.log)

        with ProcessPoolExecutor(self.processes) as executor:
            try:
                for connection_tuple in self.yieldConnectionTuple():
                    executor.submit(self.main, connection_tuple)
            except (ProtocolError, ChunkedEncodingError, IncompleteRead, ValueError):
                if self.shodan_stream:
                    LeakFinder.log.error(f"Shodan Stream: SOMETHING WENT WRONG. Retrying...\n")
                    self.wrapper()


@command()
@option_group("Hosts provider",
              option("--hosts-file", "-h",
                     help="Path to filename with hosts [IP:PORT] format, separated by a newline."),
              option("--shodan-stream", "-ss", is_flag=True, help="Get hosts using Shodan Stream API. Required to pass "
                                                                  "Shodan API in config.config file."),
              constraint=mutually_exclusive
              )
@click.option("--version-scan", "-v", is_flag=True, help="The program filters hosts to their suitable modules "
                                                         "(e.g., MongoDB, Cassandra, Elasticsearch) by comparing the  "
                                                         "module/service's default port to the host's port."
                                                         " However, sometimes there are hosts with a port different from"
                                                         " the default one (e.g., port 9201 instead of 9200 for ES),"
                                                         " and in those cases, the program can use NMAP service scan to"
                                                         " find out the host's service product, thus matching it to its"
                                                         " suitable module.")
@click.option("--patterns", "-p", help="Filter clusters by regex patterns."
                                       " Path to regex patterns file, each pattern separated by a newline.")
@click.option("--match-against", "-m", help="Where to match regex patterns.", type=click.Choice(
    ["Databases names", "Documents names", "All"], case_sensitive=False), default="All")
@click.option("--size", "-s", help="Filter clusters by size (in bytes)."
                                   " For example, to filter clusters bigger than 10MB you would pass: '{\"bigger\": "
                                   "10000000}'. To filter clusters bigger than 10MB but smaller than 100MB you would "
                                   "pass: '{\"bigger\": 10000000, \"smaller\": 100000000}'.", type=str)
@click.option("--output", "-o", is_flag=True, help="Output to file.")
@click.option("--format", "-f", "format_", help="Output file name format.", type=click.Choice(
    ["JSONLINES", "CSV", "TXT"], case_sensitive=False), default="TXT")
@click.option("--exclude-unmatched", "-eu", is_flag=True, help="Exclude non-matching clusters in output.")
@click.option("--include-geo", "-ig", is_flag=True, help="Include the IP country in output.")
@click.option("--processes", help="Number of processes. Default 1", type=int, default=1)
@click.option("--try-default", "-t", is_flag=True, help="If authentication to the cluster fail, try to login with "
                                                        "default credentials.")
@click.option("--shodan-vulns", "-sv", is_flag=True, help="To get vulnerabilities of matched clusters Shodan API key "
                                                          "is required. Insert the Shodan key in config.config file, "
                                                          "and pass this flag.")
@click.option("--silent", is_flag=True, help="No terminal output.")
def main(hosts_file, shodan_stream, version_scan, patterns, match_against, size, output, format_, exclude_unmatched,
         include_geo,
         processes, try_default, shodan_vulns, silent):
    leak_finder = LeakFinder(hosts_file, shodan_stream, version_scan, patterns, match_against, size, output, format_,
                             exclude_unmatched, include_geo,
                             processes, try_default, shodan_vulns, silent)
    leak_finder.wrapper()


if __name__ == "__main__":
    main()
