import jsonlines
from csv import DictWriter
from pathlib import Path
from math import log2
from rich.console import Console
from rich.text import Text
from geolite2 import geolite2
from flag import flagize
from Logging import log_setup


def valid_file(filepath, option, log):  # sourcery skip: merge-nested-ifs
    if filepath:
        if not Path(filepath).is_file():
            log.critical(f"INVALID FILE PATH --{option}.")
            exit()


_suffixes = ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']


# Kudos to Jules G.M. and akaIDIOT https://stackoverflow.com/a/25613067/11668025
def human_readable_size(size):
    if size < 0:
        return size
    # determine binary order in steps of size 10
    # (coerce to int, // still returns a float)
    order = int(log2(size) / 10) if size else 0
    # format file size
    # (.4g results in rounded numbers for exact matches and max 3 decimals,
    # should never resort to exponent values)
    return '{:.4g} {}'.format(size / (1 << (order * 10)), _suffixes[order])


class Output(object):
    write_instance = 0
    log = log_setup(__name__)
    console = Console()
    geo = geolite2.reader()

    def __init__(self, info, filename, output, format_, exclude_unmatched, include_geo, silent):
        self.info = info
        self.filename = filename
        self.output = output
        self.format_ = format_
        self.exclude_unmatched = exclude_unmatched
        self.include_geo = include_geo
        self.silent = silent

        self.sep = "[bold red]MATCHED" if self.info["matched_against"] else "[bold red]"
        self.data_to_write = self.get_data_to_write()
        self.country_iso_code = None
        self.output_manager()

    def output_manager(self):
        if not self.silent:
            self.terminal_output()
        if self.output:
            self.write()

    def terminal_output(self):
        Output.console.rule(self.sep)
        for key, value in self.data_to_write.items():
            key = Text(key)
            key.stylize("bold")
            if str(key) == "Vulnerabilities":
                if len(value) > 30:
                    value = value[:30]
                value = ', '.join(value)
            elif str(key) == "Hostnames":
                if len(value) > 3:
                    value = value[:3]
                value = ', '.join(value)
            Output.console.print(key + f": {value}\n")

    def get_data_to_write(self):
        data = {"Host": self.info.get("host"), "Port": self.info.get("port")}

        hostnames = self.info.get("hostnames")
        if hostnames:
            data["Hostnames"] = hostnames

        data.update({"Cluster Size": human_readable_size(self.info.get("cluster_size")), "Module": self.info.get("module")})

        if self.info.get("matches"):
            matches = self.info.get("matches")[:30]
            if len(matches) > 50:
                matches = matches[:50]
                data["Matches"] = f"{', '.join(matches)}..."
            else:
                data["Matches"] = f"{', '.join(matches)}"
            data["Matched Against"] = ', '.join(self.info.get("matched_against"))

        if self.include_geo:
            self.country_iso_code = Output.geo.get(self.info.get("host")).get("country").get("iso_code")
            data["Country"] = f"{self.country_iso_code} {flagize(f':{self.country_iso_code}:')}"

        if self.info.get("login_credentials"):
            data["Login Credentials"] = self.info.get("login_credentials")

        if self.info.get("vulnerabilities"):
            data["Vulnerabilities"] = self.info.get("vulnerabilities")
        return data

    def write(self):
        if self.format_ == "TXT":
            with open(f"{self.filename}.txt", "a+") as f:
                f.write(f"{'^' * 110}\n")
                for key, value in self.data_to_write.items():
                    if isinstance(value, list):
                        value = ", ".join(value)
                    f.write(f"{key}: {value}\n")
        elif self.format_ == "JSONLINES":
            # mode 'a' == 'a+'
            with jsonlines.open(f"{self.filename}.jsonl", mode='a') as writer:
                writer.write(self.data_to_write)
        else:
            with open(f"{self.filename}.csv", mode='a') as csv_file:
                writer = DictWriter(csv_file, fieldnames=['Host', 'Port', 'Cluster Size', 'Module', 'Matches',
                                                          'Matched Against', 'Country'])
                if Output.write_instance == 0:
                    writer.writeheader()
                writer.writerow(self.data_to_write)
                Output.write_instance += 1
