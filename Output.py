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


_suffixes = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']


def human_readable_size(size):
    # determine binary order in steps of size 10
    # (coerce to int, // still returns a float)
    order = int(log2(size) / 10) if size else 0
    # format file size
    # (.4g results in rounded numbers for exact matches and max 3 decimals,
    # should never resort to exponent values)
    return '{:.4g} {}'.format(size / (1 << (order * 10)), _suffixes[order])


class Output:
    log = log_setup(__name__)
    console = Console()
    geo = geolite2.reader()

    def __init__(self, info, filename, output, format_, include_matching, include_geo, silent):
        self.info = info
        self.filename = filename
        self.output = output
        self.format_ = format_
        self.include_matching = include_matching
        self.include_geo = include_geo
        self.silent = silent

        self.sep = "[bold red]MATCHED" if self.info["matched_against"] else "[bold red]"
        self.data_to_write = self.get_data_to_write()
        self.country_iso_code = None
        self.output_manager()

    def output_manager(self):
        if self.silent:
            self.terminal_output()
        if self.output:
            self.write()

    def terminal_output(self):
        Output.console.rule(self.sep)
        for key, value in self.data_to_write.items():
            key = Text(key)
            key.stylize("bold")
            Output.console.print(key + f": {value}\n")

    def get_data_to_write(self):
        data = {"Host": self.info.get("host"), "Port": self.info.get("port"),
                "Cluster Size": human_readable_size(self.info.get("cluster_size")), "Module": self.info.get("module")}

        if self.info.get("matches") and self.include_matching:
            matches = self.info.get("matches")[:50]
            if len(matches) > 50:
                matches = matches[:50]
                data["Matches"] = f"{', '.join(matches)}..."
            else:
                data["Matches"] = f"{', '.join(matches)}"
            data["Matched Against"] = ', '.join(self.info.get("matched_against"))

        if self.include_geo:
            self.country_iso_code = Output.geo.get(self.info.get("host")).get("country").get("iso_code")
            data["Country"] = f"{self.country_iso_code} {flagize(f':{self.country_iso_code}:')}"
        return data

    def write(self):
        if self.format_ == "TXT":
            with open(f"{self.filename}.txt", "a+") as f:
                f.write(f"{self.sep}\n")
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
                writer = DictWriter(csv_file, fieldnames=self.data_to_write.keys())
                writer.writeheader()
                writer.writerow(self.data_to_write)
