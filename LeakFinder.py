import click
from importlib import import_module
from Output import Output, valid_file
from Filter import Filter
from datetime import datetime
from Logging import log_setup
from concurrent.futures import ProcessPoolExecutor
from Shodan import Shodan
import nmap3

log = log_setup("LeakFinder")
cluster_ip = {"3306": "MySQL", "27017": "MongoDB", "9200": "ElasticSearch", "9042": "Cassandra"}
filename = datetime.now().strftime("%m.%d.%Y %H:%M:%S")
nmap = nmap3.Nmap()


def get_cluster_object(host, port, version_scan):
    module_name = cluster_ip.get(port)
    if not module_name:
        if version_scan:
            log.warning(f"Port {port} is not linked with any module. Trying NMAP service scan...")
            module_name = [module_name for module_name in cluster_ip.values() if
                           module_name.lower() in get_service(host, port).lower()]
            if module_name:
                module_name = module_name[-1]
            else:
                log.warning(f"Port {port} is not linked with any module. Available modules by host ports \n{cluster_ip}"
                            )
        else:
            log.warning(f"Port {port} is not linked with any module. Available modules by host ports \n{cluster_ip}")
    module = import_module(f"API.{module_name}")
    return getattr(module, module_name), module_name


def cluster_method_manager(cluster_instance, patterns, match_against):
    if patterns:
        if match_against == "Databases names":
            cluster_instance.list_database_names()
        elif match_against == "Documents names":
            cluster_instance.list_collections_names()
        else:
            cluster_instance.list_database_names()
            cluster_instance.list_collections_names()
    cluster_instance.get_total_size()


def read_gen(filepath):
    with open(filepath, "r") as f:
        yield from f


def return_matched_against(matched_against_dict):
    return [key.replace("_", " ").title() for key, value in matched_against_dict.items() if value]


def info_builder(host, port, cluster_obj, filter_obj, module_name, shodan):
    # Returns a dictionary for class Output
    info = {"host": host, "port": port, "cluster_size": cluster_obj.cluster_size, "module": module_name}
    if filter_obj.pattern_match:
        info["matches"] = filter_obj.matches
    info["matched_against"] = return_matched_against({"regex_match": filter_obj.pattern_match,
                                                      "size_match": filter_obj.size_match})
    if module_name in ("Cassandra", "MySQL") and cluster_obj.login_credentials:
        info["login_credentials"] = str(cluster_obj.login_credentials).replace("{", "").replace("}", "")
    s = Shodan(host, shodan)
    if not s.error and not s.cancel:
        info["vulnerabilities"] = s.get_vulns()
    return info


def get_service(host, port):
    try:
        results = nmap.scan_top_ports(host, args=f"-sV -Pn -p {port}")
        return results.get(host).get("ports")[0].get("service").get("product")
    except Exception:
        pass


def main(host, port, patterns, match_against, size, output, format_, exclude_unmatched, include_geo, try_default,
         shodan, version_scan, silent):
    cluster_obj, module_name = get_cluster_object(host, str(port), version_scan)
    cluster_instance = cluster_obj(host, port, try_default)
    if not cluster_instance.error:
        cluster_method_manager(cluster_instance, patterns, match_against)
        filter_obj = Filter(cluster_instance, patterns, match_against, size)
        if not exclude_unmatched or any(
                (filter_obj.pattern_match, filter_obj.size_match)
        ):
            Output(info_builder(host, port, cluster_instance, filter_obj, module_name, shodan), f"OUTPUT {filename}",
                   output, format_, exclude_unmatched, include_geo, silent)


@click.command()
@click.option("--hosts-file", "-h", help="Path to filename with hosts [IP:PORT] format, separated by a newline.",
              required=True)
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
@click.option("--shodan", "-sn", help="To get vulnerabilities of matched clusters Shodan API key is required."
                                      " Either pass as a CLI argument or input the API key at config.config file.")
@click.option("--silent", is_flag=True, help="No terminal output.")
def wrapper(hosts_file, version_scan, patterns, match_against, size, output, format_, exclude_unmatched, include_geo,
            processes, try_default, shodan, silent):
    valid_file(patterns, "patterns", log)
    valid_file(hosts_file, "hosts_file", log)

    executor = ProcessPoolExecutor(processes)
    for line in read_gen(hosts_file):
        line = line.strip().split(":")
        host, port = line[0], int(line[1])
        executor.submit(main, host, port, patterns, match_against, size, output, format_, exclude_unmatched,
                        include_geo, try_default, shodan, version_scan, silent)


# TODO: add an option to parse hosts from other formats, (CSV, JSON)
if __name__ == "__main__":
    wrapper()
